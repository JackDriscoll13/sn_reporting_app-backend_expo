from fastapi import APIRouter, Depends
import json 
import sys 

# Models 
from models.api_responses import StandardAPIResponse
import boto3

# Dependencies
from dependencies import get_s3_client

router = APIRouter()

# Returns our Coverage Map Data.
@router.get("/coverage_snzips", response_model=StandardAPIResponse)
def get_snzips(s3_client: boto3.client = Depends(get_s3_client)):
    # Loginto the aws session 
    try:
        print('Downloading Object')
        s3_object = s3_client.get_object(Bucket='coveragemapdata', Key='SNzips_no_sub_data.geoJSON')
        s3_object_body = s3_object['Body'].read()
        sn_zips_json = json.loads(s3_object_body)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return StandardAPIResponse(success=False, message="Failed to retrieve coverage data", data=None)
    # grab the size of the data in bytes
    snzips_size = str(sys.getsizeof(sn_zips_json['features'])) + ' bytes'
    print(snzips_size)
    return StandardAPIResponse(success=True, message="Coverage data retrieved successfully",
                                data=sn_zips_json, metadata={'size': snzips_size})

@router.get("/tester")
def tester():
    return StandardAPIResponse(success=True, message="Coverage data retrieved successfully",
                                data='test', metadata={'size': 'none'})