from contextlib import asynccontextmanager
from fastapi import FastAPI
from db import init_db
import handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB before starting API service."""
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_api_route('/api/search_places', handler.handle_get_search_places, methods=['GET'], status_code=200)
app.add_api_route('/api/current', handler.handle_post_current, methods=['POST'], status_code=201)
app.add_api_route('/api/temperature', handler.handle_post_temperature, methods=['POST'], status_code=201)
app.add_api_route('/api/current/{request_id}', handler.handle_get_current, methods=['GET'], status_code=200)
app.add_api_route('/api/temperature/{request_id}', handler.handle_get_temperature, methods=['GET'], status_code=200)
app.add_api_route('/api/currents', handler.handle_get_currents, methods=['GET'], status_code=200)
app.add_api_route('/api/temperatures', handler.handle_get_temperatures, methods=['GET'], status_code=200)
app.add_api_route('/api/current/{request_id}', handler.handle_patch_current, methods=["PATCH"], status_code=200)
app.add_api_route('/api/temperature/{request_id}', handler.handle_patch_temperature, methods=["PATCH"], status_code=200)
app.add_api_route('/api/current/{request_id}', handler.handle_delete_current, methods=["DELETE"], status_code=204)
app.add_api_route('/api/temperature/{request_id}', handler.handle_delete_temperature, methods=["DELETE"], status_code=204)
app.add_api_route('/api/export/json', handler.handle_export_json, methods=["GET"], status_code=200)
app.add_api_route('/api/export/csv/temperature', handler.handle_export_csv_temperature, methods=["GET"], status_code=200)
app.add_api_route('/api/export/csv/current', handler.handle_export_csv_current, methods=["GET"], status_code=200)