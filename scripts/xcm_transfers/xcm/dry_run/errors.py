from substrateinterface import SubstrateInterface

from scripts.xcm_transfers.utils.log import debug_log
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain


def is_call_run_error(execution_result: dict):
    return "Error" in execution_result

def get_module_error(substrate: SubstrateInterface, module_index: int, error_index: int):
    debug_log(f"Error index: {module_index}-{error_index}")

    try:
        return substrate.metadata.get_module_error(module_index=module_index, error_index=error_index)
    except:
        # TODO there is some weird behavior that substrate returns out of range (by exactly one) index for a last polkadot xcm error
        return substrate.metadata.get_module_error(module_index=module_index, error_index=error_index-1)


def extract_dispatch_error_message(chain: XcmChain, dispatch_error) -> str:
    error_description: str

    if "Module" in dispatch_error:
        module_error = dispatch_error["Module"]

        debug_log(f"Error index raw: {module_error["error"]}")

        error_index = int(module_error["error"][2:4], 16)

        error = chain.access_substrate(
            lambda s: get_module_error(s, module_error["index"], error_index))
        error_description = str(error)
    else:
        error_description = str(dispatch_error)

    return error_description

def handle_call_run_error_execution_result(chain: XcmChain, execution_result: dict):
    error = execution_result["Error"]["error"]
    error_description = extract_dispatch_error_message(chain, error)

    raise Exception(error_description)

def is_xcm_run_error(execution_result: dict):
    return "Incomplete" in execution_result or "Error" in execution_result


def handle_xcm_run_error_execution_result(execution_result: dict):
    if "Incomplete" in execution_result:
        error = execution_result["Incomplete"]["error"]
    elif "Error" in execution_result:
        error = execution_result["Error"]["error"]
    else:
        error = execution_result

    raise Exception(str(error))
