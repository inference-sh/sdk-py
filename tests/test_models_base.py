"""Tests for Pydantic v2 base models and schema mixins (regression guards)."""

import pytest
from pydantic import BaseModel

from inferencesh.models.base import (
    BaseApp,
    BaseAppInput,
    Metadata,
    OptionalImageFieldMixin,
    OptionalVideoFieldMixin,
    OrderedSchemaModel,
)


class TestMetadata:
    def test_extra_fields_allowed(self):
        meta = Metadata(app_id="app_1", custom_key="value")
        assert meta.app_id == "app_1"
        assert meta.custom_key == "value"

    def test_update_from_dict(self):
        meta = Metadata()
        meta.update({"worker_id": "w-1", "region": "us-east"})
        assert meta.worker_id == "w-1"
        assert meta.region == "us-east"

    def test_update_from_base_model(self):
        class Other(BaseModel):
            app_variant: str = "prod"

        meta = Metadata()
        meta.update(Other())
        assert meta.app_variant == "prod"

    def test_runtime_identity_fields_default_to_none(self):
        meta = Metadata()
        assert meta.task_id is None
        assert meta.team_id is None
        assert meta.user_id is None

    def test_runtime_identity_fields_accepted_at_construction(self):
        meta = Metadata(
            task_id="task_abc",
            team_id="team_xyz",
            user_id="user_123",
        )
        assert meta.task_id == "task_abc"
        assert meta.team_id == "team_xyz"
        assert meta.user_id == "user_123"

    def test_update_sets_runtime_identity_fields(self):
        meta = Metadata()
        meta.update(
            {
                "task_id": "task_run",
                "team_id": "team_acme",
                "user_id": "user_42",
            }
        )
        assert meta.task_id == "task_run"
        assert meta.team_id == "team_acme"
        assert meta.user_id == "user_42"

    def test_model_dump_includes_runtime_identity_fields(self):
        meta = Metadata(
            app_id="app_1",
            task_id="task_abc",
            team_id="team_xyz",
            user_id="user_123",
        )
        dumped = meta.model_dump()
        assert dumped["task_id"] == "task_abc"
        assert dumped["team_id"] == "team_xyz"
        assert dumped["user_id"] == "user_123"


class TestMediaFieldMixins:
    """Guard Pydantic v2 json_schema_extra for contentMediaType."""

    def test_image_mixin_schema_has_content_media_type(self):
        class Model(OptionalImageFieldMixin):
            pass

        image_schema = Model.model_json_schema()["properties"]["image"]
        assert image_schema["contentMediaType"] == "image/*"

    def test_video_mixin_schema_has_content_media_type(self):
        class Model(OptionalVideoFieldMixin):
            pass

        video_schema = Model.model_json_schema()["properties"]["video"]
        assert video_schema["contentMediaType"] == "video/*"


class TestOrderedSchemaModel:
    def test_json_schema_preserves_field_definition_order(self):
        class OrderedInput(OrderedSchemaModel):
            alpha: str
            beta: str
            gamma: str

        props = OrderedInput.model_json_schema()["properties"]
        assert list(props.keys()) == ["alpha", "beta", "gamma"]

    def test_nested_class_field_order_via_indentation_fallback(self):
        """Nested models exercise the IndentationError fallback in _get_field_order."""

        class _Wrapper:
            class NestedInput(OrderedSchemaModel):
                first: str
                second: str

        props = _Wrapper.NestedInput.model_json_schema()["properties"]
        assert list(props.keys()) == ["first", "second"]


class TestBaseApp:
    @pytest.mark.asyncio
    async def test_run_raises_not_implemented(self):
        app = BaseApp()

        with pytest.raises(NotImplementedError, match="run method must be implemented"):
            await app.run(BaseAppInput())

    @pytest.mark.asyncio
    async def test_setup_and_unload_are_no_ops(self):
        app = BaseApp()
        await app.setup()
        await app.unload()
