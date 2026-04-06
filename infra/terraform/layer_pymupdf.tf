resource "aws_lambda_layer_version" "pymupdf" {
  filename   = "${path.module}/../../build/pymupdf_layer.zip"
  layer_name = "pymupdf-layer"

  compatible_runtimes = ["python3.12"]

  source_code_hash = filebase64sha256("${path.module}/../../build/pymupdf_layer.zip")
}