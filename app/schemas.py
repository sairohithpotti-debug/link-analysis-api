from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class LinkAnalysisRequest(BaseModel):
    url: HttpUrl = Field(..., description="Target website URL to analyze")


class CompetitorProfile(BaseModel):
    name: str
    overview: str
    category: str
    products_or_services: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class BrandCompetitorComparison(BaseModel):
    brand_name: str
    brand_overview: str
    brand_category: str
    brand_products_or_services: list[str] = Field(default_factory=list)
    competitors: list[CompetitorProfile] = Field(
        default_factory=list,
        description="At least 3 competitors when reliable information can be identified",
    )
    brand_strengths: list[str] = Field(default_factory=list)
    brand_weaknesses: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    positioning_opportunities: list[str] = Field(default_factory=list)


PlatformName = Literal[
    "Google Search",
    "Facebook",
    "Instagram",
    "LinkedIn",
    "X (Twitter)",
]


class TargetSearchQuery(BaseModel):
    query: str
    platform: PlatformName
    search_intent: str
    business_relevance: str
    target_audience: str


class ContentIdea(BaseModel):
    format: Literal["Landing Page", "FAQ", "Blog Post", "Case Study", "Guide"]
    title: str
    angle: str


class SeoImprovement(BaseModel):
    primary_keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    business_keywords: list[str] = Field(default_factory=list)
    recommended_seo_title: str
    recommended_meta_description: str
    supporting_content_ideas: list[ContentIdea] = Field(default_factory=list)


class ServiceItem(BaseModel):
    name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    is_inferred: bool = Field(
        default=False,
        description="True if inferred beyond explicit page text",
    )


class TargetAudienceIdentification(BaseModel):
    primary_audiences: list[str] = Field(default_factory=list)
    secondary_audiences: list[str] = Field(default_factory=list)
    industry_segments: list[str] = Field(default_factory=list)
    business_types: list[str] = Field(default_factory=list)
    customer_profiles: list[str] = Field(default_factory=list)
    location: str | None = None
    needs_and_challenges: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    marketing_segments: list[str] = Field(default_factory=list)


class LinkAnalysisResponse(BaseModel):
    source_url: str
    final_url: str
    model_used: str
    section_1_brand_vs_competitors: BrandCompetitorComparison
    section_2_top_target_search_queries: list[TargetSearchQuery] = Field(
        description="Top 5 target search queries across Google Search, Facebook, Instagram, LinkedIn, and X (Twitter)"
    )
    section_3_seo_improvement: SeoImprovement
    section_4_top_5_services: list[ServiceItem] = Field(
        description="Top 5 services offered or inferred for the website"
    )
    section_5_target_audience: TargetAudienceIdentification
