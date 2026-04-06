resource "aws_lambda_layer_version" "openai" {
  filename   = "${path.module}/../../build/openai_layer.zip"
  layer_name = "openai-layer"

  compatible_runtimes = ["python3.12"]

  source_code_hash = filebase64sha256("${path.module}/../../build/openai_layer.zip")
}

