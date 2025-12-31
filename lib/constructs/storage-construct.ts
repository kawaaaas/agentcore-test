import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cdk from 'aws-cdk-lib/core';
import { Construct } from 'constructs';

/**
 * StorageConstruct のプロパティ
 */
export interface StorageConstructProps {
  /**
   * リソース名のプレフィックス（オプション）
   */
  readonly prefix?: string;
}

/**
 * ストレージリソースを管理する Construct
 * - Transcript_Bucket: 書き起こしテキスト保存用
 * - Minutes_Bucket: 議事録保存用
 * - Session_Table: セッション状態管理用
 */
export class StorageConstruct extends Construct {
  /**
   * 書き起こしファイル用 S3 バケット
   */
  public readonly transcriptBucket: s3.Bucket;

  /**
   * 議事録ファイル用 S3 バケット
   */
  public readonly minutesBucket: s3.Bucket;

  /**
   * セッション管理用 DynamoDB テーブル
   */
  public readonly sessionTable: dynamodb.TableV2;

  constructor(scope: Construct, id: string, props?: StorageConstructProps) {
    super(scope, id);

    const prefix = props?.prefix ?? '';

    // Transcript_Bucket: 書き起こしテキスト保存用
    // Requirements: 2.1, 2.3, 2.6, 3.4
    this.transcriptBucket = new s3.Bucket(this, 'TranscriptBucket', {
      bucketName: prefix ? `${prefix}-transcript-bucket` : undefined,
      eventBridgeEnabled: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Minutes_Bucket: 議事録保存用
    // Requirements: 2.2, 2.3, 2.6
    this.minutesBucket = new s3.Bucket(this, 'MinutesBucket', {
      bucketName: prefix ? `${prefix}-minutes-bucket` : undefined,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Session_Table: セッション状態管理用
    // Requirements: 2.4, 2.5, 2.6, 2.7
    this.sessionTable = new dynamodb.TableV2(this, 'SessionTable', {
      tableName: prefix ? `${prefix}-session-table` : undefined,
      partitionKey: {
        name: 'sessionId',
        type: dynamodb.AttributeType.STRING,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
  }
}
