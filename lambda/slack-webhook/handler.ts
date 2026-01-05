/**
 * Slack Webhook Lambda Handler
 *
 * Slack からのインタラクションイベントを受信し、署名検証を行い、
 * AgentCore Runtime に通知する Lambda 関数。
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 3.4
 */

import { InvokeCommand, LambdaClient } from "@aws-sdk/client-lambda";
import type {
  APIGatewayProxyEvent,
  APIGatewayProxyResult,
  Context,
} from "aws-lambda";
import * as crypto from "node:crypto";

// Lambda クライアントの初期化
const lambdaClient = new LambdaClient({});

/**
 * Slack インタラクションペイロード型
 */
interface SlackInteractionPayload {
  type: string;
  user: {
    id: string;
    username: string;
  };
  actions?: Array<{
    action_id: string;
    value: string;
  }>;
  view?: {
    callback_id: string;
    state: {
      values: Record<string, Record<string, { value: string }>>;
    };
  };
  response_url?: string;
  trigger_id?: string;
}

/**
 * URL 検証リクエスト型
 */
interface SlackUrlVerification {
  type: "url_verification";
  challenge: string;
}

/**
 * Slack リクエストの署名を検証する
 *
 * Requirements: 9.2, 9.3
 *
 * Slack Signing Secret を使用して HMAC-SHA256 署名を検証する。
 * タイムスタンプが 5 分以内であることも確認する。
 *
 * @param timestamp - リクエストのタイムスタンプ（X-Slack-Request-Timestamp）
 * @param body - リクエストボディ
 * @param signature - Slack の署名（X-Slack-Signature）
 * @param signingSecret - Slack Signing Secret
 * @returns 署名が有効な場合 true、無効な場合 false
 */
function verifySignature(
  timestamp: string,
  body: string,
  signature: string,
  signingSecret: string
): boolean {
  // タイムスタンプ検証（5分以内）(Requirement 9.2)
  const TIMESTAMP_TOLERANCE = 300; // 5分

  try {
    const requestTimestamp = Number.parseInt(timestamp, 10);
    const currentTimestamp = Math.floor(Date.now() / 1000);

    if (Math.abs(currentTimestamp - requestTimestamp) > TIMESTAMP_TOLERANCE) {
      console.warn("Timestamp expired", {
        requestTimestamp,
        currentTimestamp,
        diff: Math.abs(currentTimestamp - requestTimestamp),
      });
      return false;
    }
  } catch (error) {
    console.error("Invalid timestamp format:", error);
    return false;
  }

  // 署名検証（HMAC-SHA256）(Requirement 9.3)
  const sigBasestring = `v0:${timestamp}:${body}`;

  const mySignature = `v0=${crypto
    .createHmac("sha256", signingSecret)
    .update(sigBasestring)
    .digest("hex")}`;

  // タイミング攻撃を防ぐため、crypto.timingSafeEqual を使用
  try {
    const mySignatureBuffer = Buffer.from(mySignature);
    const signatureBuffer = Buffer.from(signature);

    if (mySignatureBuffer.length !== signatureBuffer.length) {
      return false;
    }

    return crypto.timingSafeEqual(mySignatureBuffer, signatureBuffer);
  } catch (error) {
    console.error("Error comparing signatures:", error);
    return false;
  }
}

/**
 * AgentCore Runtime に非同期でインタラクションイベントを通知する
 *
 * Requirements: 9.6, 3.4
 *
 * Slack の 3 秒制限に対応するため、この関数は非同期で実行される。
 * Lambda の実行は継続されるが、API Gateway へのレスポンスは即座に返される。
 *
 * @param payload - インタラクションペイロード
 */
async function notifyAgentCoreRuntime(
  payload: SlackInteractionPayload
): Promise<void> {
  const runtimeFunctionName = process.env.AGENTCORE_RUNTIME_FUNCTION_NAME;

  if (!runtimeFunctionName) {
    console.error(
      "AGENTCORE_RUNTIME_FUNCTION_NAME environment variable not set"
    );
    throw new Error("Runtime function name not configured");
  }

  try {
    console.log("Notifying AgentCore Runtime", {
      functionName: runtimeFunctionName,
      interactionType: payload.type,
    });

    // AgentCore Runtime を非同期で呼び出す
    const command = new InvokeCommand({
      FunctionName: runtimeFunctionName,
      InvocationType: "Event", // 非同期呼び出し
      Payload: JSON.stringify({
        source: "slack-webhook",
        interactionType: payload.type,
        payload: payload,
      }),
    });

    await lambdaClient.send(command);

    console.log("Successfully notified AgentCore Runtime");
  } catch (error) {
    console.error("Error notifying AgentCore Runtime:", error);
    throw error;
  }
}

/**
 * Lambda ハンドラー
 *
 * Requirements: 9.4
 *
 * @param event - API Gateway イベント
 * @param context - Lambda コンテキスト
 * @returns API Gateway レスポンス
 */
export async function handler(
  event: APIGatewayProxyEvent,
  context: Context
): Promise<APIGatewayProxyResult> {
  console.log("Received Slack webhook event", {
    requestId: context.awsRequestId,
    headers: event.headers,
  });

  try {
    // リクエストボディの取得
    if (!event.body) {
      return createErrorResponse(400, "Missing request body");
    }

    // ヘッダーの取得（大文字小文字を考慮）
    const headers = normalizeHeaders(event.headers);
    const timestamp = headers["x-slack-request-timestamp"];
    const signature = headers["x-slack-signature"];

    if (!timestamp || !signature) {
      return createErrorResponse(400, "Missing required headers");
    }

    // 署名検証（タスク 7.3）
    // Requirements: 9.2, 9.3
    const signingSecret = process.env.SLACK_SIGNING_SECRET;
    if (!signingSecret) {
      console.error("SLACK_SIGNING_SECRET environment variable not set");
      return createErrorResponse(500, "Server configuration error");
    }

    const isValid = verifySignature(
      timestamp,
      event.body,
      signature,
      signingSecret
    );
    if (!isValid) {
      console.warn("Invalid signature or expired timestamp");
      return createErrorResponse(401, "Invalid signature");
    }

    // リクエストタイプの判定
    // Content-Type が application/json の場合は URL 検証
    // application/x-www-form-urlencoded の場合はインタラクション
    const contentType = headers["content-type"] || "";

    if (contentType.includes("application/json")) {
      // URL 検証処理（タスク 7.2 で実装）
      return handleUrlVerification(event.body);
    }

    if (contentType.includes("application/x-www-form-urlencoded")) {
      // インタラクション処理（タスク 7.4 で実装）
      return await handleInteraction(event.body);
    }

    return createErrorResponse(400, "Unsupported content type");
  } catch (error) {
    console.error("Error processing Slack webhook:", error);
    return createErrorResponse(500, "Internal server error");
  }
}

/**
 * ヘッダーを正規化（小文字に変換）
 *
 * @param headers - 元のヘッダー
 * @returns 正規化されたヘッダー
 */
function normalizeHeaders(
  headers: Record<string, string | undefined>
): Record<string, string> {
  const normalized: Record<string, string> = {};
  for (const [key, value] of Object.entries(headers)) {
    if (value !== undefined) {
      normalized[key.toLowerCase()] = value;
    }
  }
  return normalized;
}

/**
 * URL 検証リクエストを処理
 *
 * Requirements: 9.5
 *
 * @param body - リクエストボディ
 * @returns チャレンジレスポンス
 */
function handleUrlVerification(body: string): APIGatewayProxyResult {
  try {
    const payload = JSON.parse(body) as SlackUrlVerification;

    // type が url_verification であることを確認
    if (payload.type !== "url_verification") {
      return createErrorResponse(400, "Invalid verification request");
    }

    // challenge が存在することを確認
    if (!payload.challenge) {
      return createErrorResponse(400, "Missing challenge parameter");
    }

    console.log("URL verification successful");

    // チャレンジ値をそのまま返す
    return createSuccessResponse({ challenge: payload.challenge });
  } catch (error) {
    console.error("Error parsing URL verification request:", error);
    return createErrorResponse(400, "Invalid JSON payload");
  }
}

/**
 * インタラクションイベントを処理
 *
 * Requirements: 9.6, 3.4
 *
 * Slack からのインタラクションイベント（ボタンクリック、モーダル送信等）を
 * パースし、AgentCore Runtime に通知する。
 *
 * 3秒以内の応答が必要なため、即座に 200 OK を返し、
 * Runtime への通知は非同期で行う（タスク 7.5 で実装）。
 *
 * @param body - リクエストボディ（application/x-www-form-urlencoded）
 * @returns 即時レスポンス（200 OK）
 */
async function handleInteraction(body: string): Promise<APIGatewayProxyResult> {
  try {
    // URL エンコードされたボディをパース
    const params = new URLSearchParams(body);
    const payloadStr = params.get("payload");

    if (!payloadStr) {
      return createErrorResponse(400, "Missing payload parameter");
    }

    // ペイロードをパース
    const payload = JSON.parse(payloadStr) as SlackInteractionPayload;

    console.log("Received interaction event", {
      type: payload.type,
      user: payload.user?.username,
      hasActions: !!payload.actions,
      hasView: !!payload.view,
    });

    // インタラクションタイプの検証
    if (!payload.type) {
      return createErrorResponse(400, "Missing interaction type");
    }

    // AgentCore Runtime への通知（非同期）
    // Requirements: 9.6, 3.4
    //
    // 即座に 200 OK を返すため、通知は非同期で実行する。
    // エラーが発生してもクライアントには影響しない。
    notifyAgentCoreRuntime(payload).catch((error) => {
      console.error("Error notifying AgentCore Runtime:", error);
    });

    // 即座に 200 OK を返す（Requirement 3.4）
    console.log("Returning immediate 200 OK response");
    return createSuccessResponse({ ok: true });
  } catch (error) {
    console.error("Error processing interaction:", error);
    return createErrorResponse(400, "Invalid interaction payload");
  }
}

/**
 * エラーレスポンスを作成
 *
 * @param statusCode - HTTP ステータスコード
 * @param message - エラーメッセージ
 * @returns API Gateway レスポンス
 */
function createErrorResponse(
  statusCode: number,
  message: string
): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ error: message }),
  };
}

/**
 * 成功レスポンスを作成
 *
 * @param body - レスポンスボディ
 * @returns API Gateway レスポンス
 */
function createSuccessResponse(body: object): APIGatewayProxyResult {
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
}
