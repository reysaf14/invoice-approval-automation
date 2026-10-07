"""Static checks for the single-input provider-neutral AI ingestion workflow."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "n8n-workflows" / "01-invoice-ingestion.json"


def load_workflow():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_has_one_drive_input_and_no_gmail_input():
    workflow = load_workflow()
    types = [node["type"] for node in workflow["nodes"]]

    assert types.count("n8n-nodes-base.googleDriveTrigger") == 1
    assert "n8n-nodes-base.gmailTrigger" not in types
    assert "n8n-nodes-base.merge" not in types


def test_workflow_uses_provider_neutral_deepseek_vision_and_normalization():
    workflow = load_workflow()
    nodes = {node["name"]: node for node in workflow["nodes"]}

    vision = nodes["AI Vision OCR"]["parameters"]
    builder = nodes["Build Vision Request"]["parameters"]
    normalizer = nodes["AI Invoice Normalizer"]["parameters"]

    assert vision["url"] == "={{$env.DEEPSEEK_API_URL}}"
    assert vision["specifyBody"] == "json"
    assert "request_body" in vision["jsonBody"]
    assert "getBinaryDataBuffer" in builder["jsCode"]
    assert "image_url" in builder["jsCode"]
    assert "$binary.data.data" not in builder["jsCode"]
    assert normalizer["url"] == "={{$env.DEEPSEEK_API_URL}}"
    assert normalizer["specifyHeaders"] == "keypair"
    assert "DEEPSEEK_API_KEY" in normalizer["headerParameters"]["parameters"][0]["value"]


def test_drive_input_is_image_only_for_ai_path():
    workflow = load_workflow()
    trigger = next(node for node in workflow["nodes"] if node["name"] == "Google Drive Trigger")
    image_filter = next(node for node in workflow["nodes"] if node["name"] == "Image File Filter")

    assert trigger["parameters"]["triggerOn"] == "specificFolder"
    assert trigger["parameters"]["event"] == "fileCreated"
    assert "jpg" in image_filter["parameters"]["jsCode"]
    assert "jpeg" in image_filter["parameters"]["jsCode"]
    assert "png" in image_filter["parameters"]["jsCode"]
    assert "pdf" not in image_filter["parameters"]["jsCode"].lower()


def test_ai_nodes_are_connected_in_order():
    workflow = load_workflow()
    connections = workflow["connections"]

    assert connections["Google Drive Trigger"]["main"][0][0]["node"] == "Image File Filter"
    assert connections["Image File Filter"]["main"][0][0]["node"] == "Download File"
    assert connections["Download File"]["main"][0][0]["node"] == "Build Vision Request"
    assert connections["Build Vision Request"]["main"][0][0]["node"] == "AI Vision OCR"
    assert connections["AI Vision OCR"]["main"][0][0]["node"] == "AI Invoice Normalizer"
    assert connections["AI Invoice Normalizer"]["main"][0][0]["node"] == "Parse DeepSeek Response"


def test_google_sheets_read_uses_v4_document_schema():
    workflow = load_workflow()
    node = next(node for node in workflow["nodes"] if node["name"] == "Read Existing Invoices")
    params = node["parameters"]

    assert params["operation"] == "read"
    assert params["documentId"]["value"] == "={{$env.GOOGLE_SHEETS_SPREADSHEET_ID}}"
    assert params["documentId"]["mode"] == "id"
    assert params["sheetName"]["value"] == "Invoices"
    assert params["sheetName"]["mode"] == "name"
    assert "sheetId" not in params
    assert node["alwaysOutputData"] is True


def test_telegram_message_reads_chat_id_from_runtime_env():
    workflow = load_workflow()
    node = next(node for node in workflow["nodes"] if node["name"] == "Build Telegram Message")
    code = node["parameters"]["jsCode"]

    assert "String($env.TELEGRAM_OWNER_CHAT_ID || '')" in code
    assert "chatId: '={{$env.TELEGRAM_OWNER_CHAT_ID}}'" not in code


def test_drive_download_retries_transient_api_failures():
    workflow = load_workflow()
    node = next(node for node in workflow["nodes"] if node["name"] == "Download File")

    assert node["retryOnFail"] is True
    assert node["maxTries"] == 3
    assert node["waitBetweenTries"] == 2000
