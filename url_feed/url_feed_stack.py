import os
from os.path import join
import json
from datetime import datetime, timezone

from aws_cdk import (
    Duration,
    Stack,
    Tags,
    RemovalPolicy,
    CfnOutput,
    # CustomResource,
    # aws_ec2 as ec2,
    aws_iam as iam,
    aws_apigateway as apigw,
    # aws_elasticloadbalancingv2 as elbv2,
    # aws_autoscaling as autoscaling,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_logs as logs,
    # aws_sns as sns,
    aws_s3 as s3,
    aws_kms as kms,
    # aws_s3_assets as s3_assets,
    aws_ssm as ssm,
    # custom_resources as cr,
)
from constructs import Construct


class UrlFeedStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # perm boundary
        # bucket
        # SSM param
        # lambda
        # restapi

        permissions_boundary_policy_arn = self.node.try_get_context(
            "PermissionsBoundaryPolicyArn"
        )

        if not permissions_boundary_policy_arn:
            permissions_boundary_policy_name = self.node.try_get_context(
                "PermissionsBoundaryPolicyName"
            )
            if permissions_boundary_policy_name:
                permissions_boundary_policy_arn = self.format_arn(
                    service="iam",
                    region="",
                    account=self.account,
                    resource="policy",
                    resource_name=permissions_boundary_policy_name,
                )

        if permissions_boundary_policy_arn:
            policy = iam.ManagedPolicy.from_managed_policy_arn(
                self, "PermissionsBoundary", permissions_boundary_policy_arn
            )
            iam.PermissionsBoundary.of(self).apply(policy)

        # if a KMS key name is provided, enable bucket encryption
        kms_key_alias = self.node.try_get_context("KmsKeyAlias")
        if kms_key_alias:
            kms_params = {
                "encryption": s3.BucketEncryption.KMS,
                "bucket_key_enabled": True,
                "encryption_key": kms.Key.from_lookup(
                    self, "KmsS3Key", alias_name=kms_key_alias
                ),
            }
        else:
            kms_params = {}

        # maybe import existing bucket from other group.
        feed_bucket = s3.Bucket(
            self,
            "UrlFeedBucket",
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            event_bridge_enabled=True,
            # **kms_params
        )

        # filename as context parameter?

        url_feed_object_info = {
            "bucket_name": feed_bucket.bucket_name,
            "object_key": "badurls.txt",
        }

        bucket_ssm_param = ssm.StringParameter(
            self,
            "UrlFeedBucketParam",
            string_value=json.dumps(url_feed_object_info, indent=2),
        )

        # setting for all python Lambda functions
        runtime = _lambda.Runtime.PYTHON_3_8
        log_retention = logs.RetentionDays.ONE_WEEK
        lambda_principal = iam.ServicePrincipal("lambda.amazonaws.com")
        basic_lambda_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "service-role/AWSLambdaBasicExecutionRole"
        )
        lambda_root = "lambda"

        managed_policies = [basic_lambda_policy]

        # role and function for calling the API
        service_role = iam.Role(
            self,
            "RetrieveUrlFeedLambdaRole",
            assumed_by=lambda_principal,
            managed_policies=managed_policies,
            # inline_policies={
            #     "inlineTestApiRole": iam.PolicyDocument(
            #         assign_sids=True,
            #         statements=[
            #             allow_read_inbound_bucket_read,
            #             iam.PolicyStatement(
            #                 actions=["s3:PutObject", "s3:PutObjectTagging"],
            #                 effect=iam.Effect.ALLOW,
            #                 resources=[
            #                     outbound_bucket.bucket_arn,
            #                     outbound_bucket.arn_for_objects("*"),
            #                 ],
            #             ),
            #             iam.PolicyStatement(
            #                 actions=["events:PutEvents"],
            #                 effect=iam.Effect.ALLOW,
            #                 resources=[event_bus.event_bus_arn],
            #             ),
            #         ],
            #     )
            # },
        )

        feed_bucket.grant_read(service_role)
        bucket_ssm_param.grant_read(service_role)

        retrieve_feed_lambda = _lambda.Function(
            self,
            "RetrieveUrlFeedLambda",
            runtime=runtime,
            code=_lambda.Code.from_asset(
                os.path.join(lambda_root, "retrieve_url_feed")
            ),
            handler="retrieve_url_feed.lambda_handler",
            environment={
                # **debug_env,
                "BUCKET_SSM_PARAM": bucket_ssm_param.parameter_name,
            },
            timeout=Duration.seconds(60),
            role=service_role,
            log_retention=log_retention,
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/README.html#aws-lambda-backed-apis

        # add API gw
        feed_api = apigw.LambdaRestApi(self, "RestApi", handler=retrieve_feed_lambda)

        feed = feed_api.root.add_resource("feed")
        feed.add_method("GET")  # , apigw.LambdaIntegration(retrieve_feed_lambda)

        CfnOutput(self, "RestApiURL", value=feed_api.url)
