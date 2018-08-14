import subprocess


def upload(filename):
  # Upload to S3. Will take 24 hrs to update in CloudFront edge cache
  command = 'aws s3 cp {} s3://shyr/'.format(filename)
  subprocess.call(command.split())


def sync(src, dst):
  command = "aws s3 sync --delete --exclude '*.DS_Store*' {} s3://shyr/{}".format(src, dst)
  subprocess.call(command.split())
