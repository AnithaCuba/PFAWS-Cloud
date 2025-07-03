provider "aws" {
  region = "us-east-1"
}

# Bucket de entrada
resource "aws_s3_bucket" "input" {
  bucket = "input-bucket-covid-test"
  force_destroy = true
}

# Bucket de salida
resource "aws_s3_bucket" "output" {
  bucket = "output-bucket-covid-test"
  force_destroy = true
}

# Rol de ejecución para Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role_test01"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# Políticas para permitir a Lambda acceder a S3
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda_policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:*"]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = ["logs:*"]
        Resource = ["*"]
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "covid_cleaner" {
  filename         = "../lambda_newtest.zip"
  function_name    = "covid_test01"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("../lambda_newtest.zip")

  environment {
    variables = {
      OUTPUT_BUCKET = var.output_bucket_name
    }
  }
}

# Permitir a S3 invocar Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.covid_cleaner.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.input.arn
}

# Notificación: invocar Lambda al subir CSV
resource "aws_s3_bucket_notification" "notify_lambda" {
  bucket = aws_s3_bucket.input.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.covid_cleaner.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}