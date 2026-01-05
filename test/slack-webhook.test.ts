/**
 * Slack Webhook Lambda Handler のテスト
 *
 * Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 3.4
 */

import { LambdaClient } from "@aws-sdk/client-lambda";
import type {
  APIGatewayProxyEvent,
  APIGatewayProxyResult,
  Context,
} from "aws-lambda";
import * as crypto from "node:crypto";
import { handler } from "../lambda/slack-webhook/handler";

// Lambda クライアントのモック
jest.mock("@aws-sdk/client-lambda");

describe("Slack Webhook Lambda Handler", () => {
  const mockContext: Context = {
    awsRequestId: "test-request-id",
    callbackWaitsForEmptyEventLoop: false,
    functionName: "test-function",
    functionVersion: "1",
    invokedFunctionArn: "arn:aws:lambda:us-east-1:123456789012:function:test",
    memoryLimitInMB: "128",
    logGroupName: "/aws/lambda/test",
    logStreamName: "test-stream",
    getRemainingTimeInMillis: () => 30000,
    done: jest.fn(),
    fail: jest.fn(),
    succeed: jest.fn(),
  };

  const mockSigningSecret = "test-signing-secret";
  const mockRuntimeFunctionName = "test-runtime-function";

  beforeEach(() => {
    // 環境変数の設定
    process.env.SLACK_SIGNING_SECRET = mockSigningSecret;
    process.env.AGENTCORE_RUNTIME_FUNCTION_NAME = mockRuntimeFunctionName;

    // Lambda クライアントのモックをリセット
    jest.clearAllMocks();
  });

  afterEach(() => {
    // 環境変数のクリーンアップ
    delete process.env.SLACK_SIGNING_SECRET;
    delete process.env.AGENTCORE_RUNTIME_FUNCTION_NAME;
  });

  /**
   * 有効な Slack 署名を生成するヘルパー関数
   */
  function generateValidSignature(
    timestamp: string,
    body: string,
    secret: string
  ): string {
    const sigBasestring = `v0:${timestamp}:${body}`;
    const signature = crypto
      .createHmac("sha256", secret)
      .update(sigBasestring)
      .digest("hex");
    return `v0=${signature}`;
  }

  /**
   * テスト用の API Gateway イベントを作成
   */
  function createMockEvent(
    body: string,
    headers: Record<string, string>
  ): APIGatewayProxyEvent {
    return {
      body,
      headers,
      multiValueHeaders: {},
      httpMethod: "POST",
      isBase64Encoded: false,
      path: "/slack/events",
      pathParameters: null,
      queryStringParameters: null,
      multiValueQueryStringParameters: null,
      stageVariables: null,
      requestContext: {
        accountId: "123456789012",
        apiId: "test-api",
        protocol: "HTTP/1.1",
        httpMethod: "POST",
        path: "/slack/events",
        stage: "prod",
        requestId: "test-request",
        requestTime: "01/Jan/2025:00:00:00 +0000",
        requestTimeEpoch: Date.now(),
        identity: {
          cognitoIdentityPoolId: null,
          accountId: null,
          cognitoIdentityId: null,
          caller: null,
          sourceIp: "1.2.3.4",
          principalOrgId: null,
          accessKey: null,
          cognitoAuthenticationType: null,
          cognitoAuthenticationProvider: null,
          userArn: null,
          userAgent: "Slackbot 1.0",
          user: null,
          apiKey: null,
          apiKeyId: null,
          clientCert: null,
        },
        authorizer: null,
        resourceId: "test-resource",
        resourcePath: "/slack/events",
      },
      resource: "/slack/events",
    };
  }

  describe("URL 検証 (Requirement 9.5)", () => {
    it("有効な URL 検証リクエストに対してチャレンジを返す", async () => {
      const challenge = "test-challenge-value";
      const body = JSON.stringify({
        type: "url_verification",
        challenge,
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(200);
      expect(JSON.parse(result.body)).toEqual({ challenge });
    });

    it("challenge が欠けている場合は 400 を返す", async () => {
      const body = JSON.stringify({
        type: "url_verification",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(400);
      expect(JSON.parse(result.body).error).toContain("challenge");
    });
  });

  describe("署名検証 (Requirements 9.2, 9.3)", () => {
    it("有効な署名を持つリクエストを受け入れる", async () => {
      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(200);
    });

    it("無効な署名を持つリクエストを拒否する", async () => {
      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();
      const invalidSignature = "v0=invalid-signature";

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": invalidSignature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(401);
      expect(JSON.parse(result.body).error).toContain("signature");
    });

    it("5分以上古いタイムスタンプを拒否する (Requirement 9.2)", async () => {
      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      // 6分前のタイムスタンプ
      const oldTimestamp = (Math.floor(Date.now() / 1000) - 360).toString();
      const signature = generateValidSignature(
        oldTimestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": oldTimestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(401);
    });

    it("署名ヘッダーが欠けている場合は 400 を返す", async () => {
      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        // X-Slack-Signature が欠けている
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(400);
      expect(JSON.parse(result.body).error).toContain("headers");
    });
  });

  describe("インタラクション処理 (Requirements 9.6, 3.4)", () => {
    beforeEach(() => {
      // Lambda クライアントの send メソッドをモック
      (LambdaClient.prototype.send as jest.Mock) = jest
        .fn()
        .mockResolvedValue({});
    });

    it("ブロックアクションを処理し、即座に 200 を返す (Requirement 3.4)", async () => {
      const payload = {
        type: "block_actions",
        user: {
          id: "U123456",
          username: "testuser",
        },
        actions: [
          {
            action_id: "approve_action",
            value: "session-123",
          },
        ],
      };

      const body = `payload=${encodeURIComponent(JSON.stringify(payload))}`;
      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      // 即座に 200 OK を返す
      expect(result.statusCode).toBe(200);
      expect(JSON.parse(result.body)).toEqual({ ok: true });
    });

    it("ビュー送信を処理し、即座に 200 を返す", async () => {
      const payload = {
        type: "view_submission",
        user: {
          id: "U123456",
          username: "testuser",
        },
        view: {
          callback_id: "feedback_modal",
          state: {
            values: {
              feedback_block: {
                feedback_input: {
                  value: "修正内容",
                },
              },
            },
          },
        },
      };

      const body = `payload=${encodeURIComponent(JSON.stringify(payload))}`;
      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(200);
      expect(JSON.parse(result.body)).toEqual({ ok: true });
    });

    it("payload パラメータが欠けている場合は 400 を返す", async () => {
      const body = "invalid=data";
      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(400);
      expect(JSON.parse(result.body).error).toContain("payload");
    });
  });

  describe("エラーハンドリング", () => {
    it("リクエストボディが欠けている場合は 400 を返す", async () => {
      const event = createMockEvent("", {
        "Content-Type": "application/json",
      });
      event.body = null;

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(400);
      expect(JSON.parse(result.body).error).toContain("body");
    });

    it("SLACK_SIGNING_SECRET が設定されていない場合は 500 を返す", async () => {
      delete process.env.SLACK_SIGNING_SECRET;

      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();

      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": "v0=test",
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(500);
      expect(JSON.parse(result.body).error).toContain("configuration");
    });

    it("サポートされていない Content-Type の場合は 400 を返す", async () => {
      const body = "test";
      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      const event = createMockEvent(body, {
        "Content-Type": "text/plain",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(400);
      expect(JSON.parse(result.body).error).toContain("content type");
    });
  });

  describe("ヘッダー正規化", () => {
    it("大文字小文字を区別せずにヘッダーを処理する", async () => {
      const body = JSON.stringify({
        type: "url_verification",
        challenge: "test",
      });

      const timestamp = Math.floor(Date.now() / 1000).toString();
      const signature = generateValidSignature(
        timestamp,
        body,
        mockSigningSecret
      );

      // 大文字のヘッダー名を使用
      const event = createMockEvent(body, {
        "Content-Type": "application/json",
        "X-SLACK-REQUEST-TIMESTAMP": timestamp,
        "X-SLACK-SIGNATURE": signature,
      });

      const result: APIGatewayProxyResult = await handler(event, mockContext);

      expect(result.statusCode).toBe(200);
    });
  });
});
