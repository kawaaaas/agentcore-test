import { Template } from "aws-cdk-lib/assertions";
import * as cdk from "aws-cdk-lib/core";
import { MainStack } from "../lib/stacks/main-stack";

describe("MainStack", () => {
  test("スタックが正常に作成される", () => {
    const app = new cdk.App();
    const stack = new MainStack(app, "TestStack", {
      agentCodeBucket: "test-agent-code-bucket",
      agentCodePrefix: "agents/",
    });
    const template = Template.fromStack(stack);

    // スタックが空でも正常に作成されることを確認
    expect(template.toJSON()).toBeDefined();
  });

  test("AgentCore リソースが作成される", () => {
    const app = new cdk.App();
    const stack = new MainStack(app, "TestStack", {
      agentCodeBucket: "test-agent-code-bucket",
      agentCodePrefix: "agents/",
    });
    const template = Template.fromStack(stack);
    const resources = template.toJSON().Resources;

    // AgentCore Memory が作成されることを確認
    const memoryResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::BedrockAgentCore::Memory"
    );
    expect(memoryResources.length).toBe(1);
    expect((memoryResources[0] as any).Properties.Name).toBe(
      "MeetingAgentMemory"
    );
    expect((memoryResources[0] as any).Properties.EventExpiryDuration).toBe(90);

    // AgentCore WorkloadIdentity が作成されることを確認
    const identityResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::BedrockAgentCore::WorkloadIdentity"
    );
    expect(identityResources.length).toBe(1);
    expect((identityResources[0] as any).Properties.Name).toBe(
      "MeetingAgentIdentity"
    );

    // AgentCore Gateway が作成されることを確認
    const gatewayResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::BedrockAgentCore::Gateway"
    );
    expect(gatewayResources.length).toBe(1);
    expect((gatewayResources[0] as any).Properties.Name).toBe(
      "MeetingAgentGateway"
    );
    expect((gatewayResources[0] as any).Properties.AuthorizerType).toBe(
      "AWS_IAM"
    );
    expect((gatewayResources[0] as any).Properties.ProtocolType).toBe("MCP");

    // AgentCore Runtime が作成されることを確認
    const runtimeResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::BedrockAgentCore::Runtime"
    );
    expect(runtimeResources.length).toBe(1);
    expect((runtimeResources[0] as any).Properties.AgentRuntimeName).toBe(
      "MeetingAgentRuntime"
    );
    expect(
      (runtimeResources[0] as any).Properties.NetworkConfiguration.NetworkMode
    ).toBe("PUBLIC");

    // RuntimeEndpoint が作成されることを確認
    const endpointResources = Object.values(resources).filter(
      (r: any) => r.Type === "AWS::BedrockAgentCore::RuntimeEndpoint"
    );
    expect(endpointResources.length).toBe(1);
    expect((endpointResources[0] as any).Properties.Name).toBe(
      "default_endpoint"
    );
  });

  test("出力値が設定される", () => {
    const app = new cdk.App();
    const stack = new MainStack(app, "TestStack", {
      agentCodeBucket: "test-agent-code-bucket",
      agentCodePrefix: "agents/",
    });
    const template = Template.fromStack(stack);
    const outputs = template.toJSON().Outputs;

    // 出力値が存在することを確認
    expect(outputs.RuntimeArn).toBeDefined();
    expect(outputs.GatewayArn).toBeDefined();
    expect(outputs.MemoryId).toBeDefined();
    expect(outputs.IdentityArn).toBeDefined();
  });
});
