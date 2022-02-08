# import json
'''necessery dependencies for json logger'''
# import logging
# import os
# from pythonjsonlogger import jsonlogger
'''tracer dependency'''
# from aws_xray_sdk.core import xray_recorder,patch_all
'''necessery dependencies for metrics'''
# import os
# import boto3
'''powertool dependencies'''
from typing import List
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

# cold_start = True
# '''creating a container for all metrics'''
# metric_namespace = "MyApp"
#adding powertool logger.
logger = Logger(service = "Powertool_Logger_App")
#adding powertool tracer
tracer = Tracer(service = "Powertool_Tracer_App")
# adding powertool metric generator
metrics = Metrics(namespace="Myapp", service= "Powertool_Metric_App")
# cloudwatch client initialized
# metrics = boto3.client("cloudwatch")
'''Don't need to use any of these if we use powertool logger....'''
'''creating logger application named App'''
# logger = logging.getLogger("Json_Logger_App")
# '''declaring handler and formatter'''
# logHandler = logging.StreamHandler()
# #passing custom fields to the jsonFormatter
# formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
# logHandler.setFormatter(formatter)
# logger.addHandler(logHandler)
# '''setting the logging level in the env_variable'''
# logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
app = ApiGatewayResolver()
# cold_start = True
'''patch_all() -> ingores any libraries that are not installed'''
# patch_all() 

'''custom metrics generator'''
# @tracer.capture_method
# def add_greeting_metric(service: str = "Metric_App"):
#     function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "undefined")
#     service_dimension = {"Name": "service", "Value": service}
#     function_dimension = {"Name": "function_name", "Value": function_name}
#     is_cold_start = True

#     global cold_start
#     if cold_start:
#         cold_start = False
#     else:
#         is_cold_start = False

#     return metrics.put_metric_data(
#         MetricData = [
#             {
#                 "MetricName": "SuccessfullGreetings",
#                 "Dimensions": [service_dimension],
#                 "Unit": "Count",
#                 "Value": 1,
#             },
#             {
#                 "MetricName": "ColdStart",
#                 "Dimensions": [service_dimension, function_dimension],
#                 "Unit": "Count",
#                 "Value": int(is_cold_start)
#             }
#         ],
#         Namespace = metric_namespace,
#     )

'''creating middleware'''
@lambda_handler_decorator(trace_execution= True)
def middleware_before_after(handler, event, context):
    #logic_before_handler_execution()
    print("Saying hello before Handler is called...")
    response = handler(event, context)
    #logic_after_handler_execution()
    print("saying hello after Handler is called...")
    return response

@lambda_handler_decorator(trace_execution= True)
def hiding_sensitive_data(handler, event, context, fields: List = None):
    tracer = Tracer()
    tracer.put_annotation(key= "user", value= "Message")
    if fields:
        for field in fields:
            if field in event:
                event[field] = obfuscate(event[field])
    return handler(event, context)

@lambda_handler_decorator(trace_execution= True)
def another_middleware(handler, event, context, hello = False ):
    if hello:
        print("------ Parameter Detected ------")
    print("Saying hello before Handler is called")
    response = handler(event, context)
    print("Saying hello after Handle is called")
    return response

'''routing decorator next tracer decorator'''
@app.get("/activity/<month>")
# @xray_recorder.capture('display_month')
@tracer.capture_method
def display_month(month):
    # subsegment = xray_recorder.current_subsegment()
    # subsegment.put_annotation(key = "User", value = month)
    tracer.put_annotation(key = "User", value = month)
    logger.info(f"Request for changing month to {month} received...")
    metrics.add_metric(name = "SuccessfulGreeting", unit = MetricUnit.Count, value = 1)
    # add_greeting_metric()
    return{
        "message": f"Winter is coming in {month}...!!!"
    }
    
'''routing decorator then tracer decorator'''
@app.get("/activity")
# @xray_recorder.capture('display')
def display():
    # subsegment = xray_recorder.current_subsegment()
    # subsegment.put_annotation(key = "User", value = "Message")
    tracer.put_annotation(key = "User", value = "Message")
    logger.info("Message received...")
    metrics.add_metric(name="SuccessfulGreeting",unit=MetricUnit.Count,value=1)
    # add_greeting_metric()
    return{
        "message": "winter is coming..."
    }

'''using logger.inject_lambda_context decorator to inject key 
information from Lambda context into every log.
also setting log_event=True to automatically log each incoming request for debugging'''
@logger.inject_lambda_context(correlation_id_path = correlation_paths.API_GATEWAY_REST, log_event = True)
# @xray_recorder.capture('handler')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
@middleware_before_after
@hiding_sensitive_data(fields=["email"])
@another_middleware(hello=True)
def lambda_handler(event, context):
    # global cold_start
    # subsegment = xray_recorder.current_subsegment()
    # if cold_start:
    #     subsegment.put_annotation(key = "ColdStart", value = cold_start)
    #     cold_start = False
    # else:
    #     subsegment.put_annotation(key = "ColdStart", value = cold_start)
    # logger.debug(event)
    result = app.resolve(event, context)
    # subsegment.put_metadata("response", result)
    try:
        return result
    except Exception as e:
        logger.exception(e)
        raise

#don't need any of these if we use powertools for api routing... SOOO EASY!!!!!
# def display(**kargs):
#     return {"statusCode": 200,
#      "body": json.dumps({"message": "winter is coming"})
#     }

# def display_month(event, **kargs):
#     month = event["pathParameters"]["month"]
#     return{
#         "status code": 200,
#         "body": json.dumps({
#             "message": f"Winter is coming in {month} ....!!!"
#         })
#     }

# class Router:
#     def __init__(self) -> None:
#         self.routes = {}

#     def set(self, path, method, handler):
#         self.routes[f"{path}-{method}"] = handler
    
#     def get(self, path, method):
#         try:
#             route = self.routes[f"{path}-{method}"]
#         except KeyError:
#             raise RuntimeError(f"Cannot route request to the correct method. path={path}, method={method}")
#         return route

# router = Router()
# router.set(path="/activity",method="GET", handler="display")
# router.set(path="/activity", method="GET", handler="display_month")

# def lambda_handler(event, context):
#     path = event["resource"]
#     http_method = event["httpMethod"]
#     method = router.get(path=path, method=http_method)
#     return method(event = event)