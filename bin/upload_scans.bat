aws s3 rm s3://sebcel-receipt-analyzer-raw-bucket-dev/raw/ --recursive --profile %2
aws s3 sync %1 s3://sebcel-receipt-analyzer-raw-bucket-dev/raw/ --profile %2
