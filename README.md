# URL Feed for Cisco Secure Management Center

This CDK stack implements a URL feed for use by Cisco Secure Management Center.

[Security Intelligence Sources](https://www.cisco.com/c/en/us/td/docs/security/secure-firewall/management-center/device-config/720/management-center-device-config-72/access-security-intelligence.html)

[Security Intelligence Lists and Feeds](https://www.cisco.com/c/en/us/td/docs/security/secure-firewall/management-center/device-config/720/management-center-device-config-72/objects-object-mgmt.html#ID-2243-00000135)

# Functionality

Once deployed, the there will be a URL that will return either a feed of URLs or an MD5 hash of the URL file.
Per the Cisco documentation, the URLs must be returned in a text file, one per line. The optional MD5 hash
can be used to detect whether or not a change has occurred.

The file of URLs need to be placed in the S3 bucket. The name of file can be anything but will be used when
the complete URL is entered into the Cisco management center. The specific URL will be returned in the Cloud Formation output.

The syntax of the feed URL is as follows:

`https://<URL>/?filename=<URL filename>`

The MD5 has URL is the same except that `md5` is added as a query string parameter.

`https://<URL>/?filename=<URL filename>&md5`

The API can be tested via `curl` on the command line:

```
[~/ec/projects/ose/url-feed] | curl 'https://fapnrqdul7.execute-api.us-east-1.amazonaws.com/prod/?filename=badurls.txt'
superbadurl1.com
superbadurl2.com
superbadurl3.com
superbadurl4.com
gambling.com
[~/ec/projects/ose/url-feed] | curl 'https://fapnrqdul7.execute-api.us-east-1.amazonaws.com/prod/?filename=badurls.txt&md5'
29472b640ba9b5b765c27195bcf66e98

```

# cdk.json Variables

- PermissionsBoundaryPolicyArn (String) - The full ARN for a policy to be used as the permissions boundary policy on all roles. (Optional)
- PermissionsBoundaryPolicyName (String) - The name for a policy to be used as the permissions boundary policy on all roles. (Optional)
- Tags (Mapping) - A mapping of key/value pairs. Will be attached as tags to all taggable resources. (Optional)

# Internals

The stack creates the following resources:

- An S3 bucket
- An SSM parameter
- A lambda function
- An API gateway

# Failure conditions

- Failure to retrieve file from S3 (file missing, permission error, etc.)
- File too large. (API gateway limits payload to 10MB)
- Failure to retrieve SSM parameter.
