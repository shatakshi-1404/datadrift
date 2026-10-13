from pydantic import BaseModel


class GlobalImportanceItem(BaseModel):
    feature: str
    mean_abs_shap: float


class LocalContribution(BaseModel):
    feature: str
    contribution: float  # signed: positive pushes toward churn, negative away from it
    direction: str


class LocalExplanation(BaseModel):
    dataset_id: int
    row_index: int
    base_value: float
    predicted_probability: float
    predicted_class: int
    contributions: list[LocalContribution]


class ExplainabilityResponse(BaseModel):
    model_id: int
    global_importance: list[GlobalImportanceItem]
    local: LocalExplanation | None = None
