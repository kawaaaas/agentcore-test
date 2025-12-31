import * as events from 'aws-cdk-lib/aws-events';
import * as cdk from 'aws-cdk-lib/core';
import { Construct } from 'constructs';
import { StorageConstruct } from '../constructs/storage-construct';

/**
 * メインスタック
 * すべての Construct を組み合わせるエントリーポイント
 * Requirements: 5.1
 */
export class MainStack extends cdk.Stack {
  /**
   * ストレージリソースを管理する Construct
   */
  public readonly storage: StorageConstruct;

  /**
   * S3 PutObject イベントをトリガーする EventBridge ルール
   */
  public readonly transcriptUploadRule: events.Rule;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // StorageConstruct をインスタンス化
    // Requirements: 5.1, 5.2
    this.storage = new StorageConstruct(this, 'Storage');

    // EventBridge ルールを作成
    // Transcript_Bucket への PutObject イベントをトリガー
    // Requirements: 3.1, 3.2, 3.3
    this.transcriptUploadRule = new events.Rule(this, 'TranscriptUploadRule', {
      ruleName: 'transcript-upload-rule',
      description: 'Transcript_Bucket への書き起こしテキストアップロードを検知',
      eventPattern: {
        source: ['aws.s3'],
        detailType: ['Object Created'],
        detail: {
          bucket: {
            name: [this.storage.transcriptBucket.bucketName],
          },
        },
      },
    });
  }
}
