resource "aws_apigatewayv2_api" "receipt_api" {
  name          = "${local.project}-api-${var.environment}"
  protocol_type = "HTTP"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-api-${var.environment}"
    }
  )
}


resource "aws_apigatewayv2_integration" "upload_integration" {
  api_id = aws_apigatewayv2_api.receipt_api.id

  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.upload_url_generator_function.invoke_arn

  integration_method = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "upload_route" {
  api_id = aws_apigatewayv2_api.receipt_api.id
  route_key = "POST /receipts/upload-url"
  target = "integrations/${aws_apigatewayv2_integration.upload_integration.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_authorizer.id
}

resource "aws_lambda_permission" "api_gateway_upload_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_url_generator_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.receipt_api.execution_arn}/*/*"
}


resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.receipt_api.id
  name        = "$default"
  auto_deploy = true
}