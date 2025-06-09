# Only handle the situation when the user uploads a file, and do not handle other requests
# A new "user_request_type" field needs to be added in the request body to represent the type of the user request
user_request_type = request_body.get("user_request_type", None)
file_type = file_type.split('.')[-1]
file_path = file_path.split('/')[-1]

def lambda_handler(event, context):
    # Detect the type of user request
    if user_request_type == "detect":
        detect_result = invoke_lambda_function(file_type)
        
        lambda_client.invoke(FunctionName = "sns") # sns
        store_detect_result_dynamodb(detect_result) 
        
        # Create a thumbnail for the image
        if file_type in ["jpg", "jpeg", "png"]:
            lambda_client.invoke(FunctionName = "lambda6")
            
        return response_json(200, {
            "detected_labels": detect_result
        })
            
    elif user_request_type == "query":
        detect_result = invoke_lambda_function(file_type)
        
        tags = list(detect_result.keys()) # ["Crow", "Kingfisher"] Extract the keys in the detection results as tags
        response = query_species(tags) # Activate lambda10 to query species information
        
        # Activate lambda5 to delete the files uploaded by the user
        lambda_client.invoke(
            FunctionName = "lambda5",
            Payload=json.dumps(file_path)
        )
        
        return response
        

def invoke_lambda_function(file_type):
    # image_detection
    if file_type in ["jpg", "jpeg", "png"]:
        response = lambda_client.invoke(
            FunctionName = "lambda2"
        )
        
    # video_detection
    elif file_type in ["mp4", "avi"]:
        response = lambda_client.invoke(
            FunctionName = "lambda3"
        )
        
    # audio_detection
    elif file_type in ["mp3", "wav"]:
        response = lambda_client.invoke(
            FunctionName = "lambda4"
        )

    # Results
    detect_result = json.loads(response['Payload'].read())
    return detect_result # {"Crow": {"N": "1"}} counts of birds

# Store in DynamoDB
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
    # lambda10 payload
    species_query_event = {
        "httpMethod": "GET",
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {
            "species": tags
        },
        "headers": {},
        "body": None
    }
    
    # lmabda10
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