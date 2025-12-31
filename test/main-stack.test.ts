import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib/core';
import { MainStack } from '../lib/stacks/main-stack';

describe('MainStack', () => {
  test('スタックが正常に作成される', () => {
    const app = new cdk.App();
    const stack = new MainStack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // スタックが空でも正常に作成されることを確認
    expect(template.toJSON()).toBeDefined();
  });
});
