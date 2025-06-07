# 只处理当用户上传了文件时的情况，不处理其他request
# 需要在request body新增一个user_request_type字段，表示用户请求的类型
user_request_type = request_body.get("user_request_type", None)
file_type = file_type.split('.')[-1]
file_path = file_path.split('/')[-1]

def lambda_handler(event, context):
    # 检测用户请求类型
    if user_request_type == "detect":
        detect_result = invoke_lambda_function(file_type)
        
        lambda_client.invoke(FunctionName = "sns") # sns
        store_detect_result_dynamodb(detect_result) # 存储检测结果到DynamoDB
        
        # 给图像创建thumbnail
        if file_type in ["jpg", "jpeg", "png"]:
            lambda_client.invoke(FunctionName = "lambda6")
            
        return response_json(200, {
            "detected_labels": detect_result
        })
            
    elif user_request_type == "query":
        detect_result = invoke_lambda_function(file_type)
        
        tags = list(detect_result.keys()) # ["Crow", "Kingfisher"] 提取检测结果中的键作为tags
        response = query_species(tags) # 唤起lambda10查询物种信息
        
        # 唤起lambda5来删除用户用户上传的文件
        lambda_client.invoke(
            FunctionName = "lambda5",
            Payload=json.dumps(file_path)
        )
        
        return response
        

def invoke_lambda_function(file_type):
    # 唤起image_detection
    if file_type in ["jpg", "jpeg", "png"]:
        response = lambda_client.invoke(
            FunctionName = "lambda2"
        )
        
    # 唤起video_detection
    elif file_type in ["mp4", "avi"]:
        response = lambda_client.invoke(
            FunctionName = "lambda3"
        )
        
    # 唤起audio_detection
    elif file_type in ["mp3", "wav"]:
        response = lambda_client.invoke(
            FunctionName = "lambda4"
        )

    # 读取结果
    detect_result = json.loads(response['Payload'].read())
    return detect_result # {"Crow": {"N": "1"}} 这里有检测到的鸟的数量

# 存储检测结果到DynamoDB
def store_detect_result_dynamodb(detect_result):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('DetectResults')
    
    response = table.put_item(
        Item={
            'id': detect_result['id'],
            'file_type': detect_result['file_type'],
            'result': detect_result['result']
        }
    )
    
    return response

def query_species(tags):
    # 创建lambda10的payload
    species_query_event = {
        "httpMethod": "GET",
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {
            "species": tags
        },
        "headers": {},
        "body": None
    }
    
    # 唤起lmabda10
    response = lambda_client.invoke(
        FunctionName=query_function,
        InvocationType='RequestResponse',
        Payload=json.dumps(species_query_event)
    )
    
    query_result = json.loads(response['Payload'].read())
    query_result_body = json.loads(query_result.get("body", "{}"))
    
    thumbnail_url = None
    if key.startswith("image/"):
        filename = key.split("/")[-1]
        thumbnail_url = f"s3://{bucket}/thumbnail/{filename}"

    return response_json(200, {
        "detected_labels": tags,
        "query_by_species_result": query_result_body,
        "thumbnail_url": thumbnail_url
    })