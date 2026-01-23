#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { MainStack } from "../lib/stacks/main-stack";
import { TestStack } from "../lib/stacks/s3";



const app = new cdk.App();

const stg = new TestStack(app, "StgStack")
const prod = new TestStack(app, "ProdStack")

cdk.Tags.of(stg).add('Environment', 'Staging');
cdk.Tags.of(prod).add('Environment', 'Production');


// 環境設定
// CDK_DEFAULT_ACCOUNT と CDK_DEFAULT_REGION は cdk deploy 時に自動的に設定される
// または明示的に AWS_ACCOUNT_ID と AWS_REGION 環境変数で指定可能
// Requirements: 1.4
const env: cdk.Environment = {
  account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
  region: process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION,
};

// エージェントコードの S3 設定
// 環境変数で指定するか、デフォルト値を使用
const agentCodeBucket = process.env.AGENT_CODE_BUCKET || "meeting-agent-code";
const agentCodePrefix = process.env.AGENT_CODE_PREFIX || "agents/";

new MainStack(app, "MainStack", {
  env,
  description: "議事録・タスク管理自動化 AI エージェント インフラ基盤",
  agentCodeBucket,
  agentCodePrefix,
});


