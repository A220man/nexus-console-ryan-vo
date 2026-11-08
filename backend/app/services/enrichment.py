import json
import re
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.enrichment import EnrichmentJob, EnrichmentStatus, EnrichmentProvider, EnrichmentTargetType
from app.models.contact import Contact
from app.models.company import Company
from app.schemas.enrichment import EnrichmentResult
from app.core.config import settings


@dataclass
class EnrichmentContext:
    """Context passed to enrichment providers."""
    target_type: EnrichmentTargetType
    target_id: int
    input_data: Dict[str, Any]
    config: Dict[str, Any]


class EnrichmentProviderBase(ABC):
    """Abstract base class for enrichment providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> EnrichmentProvider:
        pass
    
    @abstractmethod
    async def enrich(self, context: EnrichmentContext) -> EnrichmentResult:
        pass


class OfflineEnrichmentProvider(EnrichmentProviderBase):
    """Deterministic offline enrichment using heuristics and public data patterns."""
    
    @property
    def provider_name(self) -> EnrichmentProvider:
        return EnrichmentProvider.OFFLINE
    
    async def enrich(self, context: EnrichmentContext) -> EnrichmentResult:
        if context.target_type == EnrichmentTargetType.CONTACT:
            return await self._enrich_contact(context)
        elif context.target_type == EnrichmentTargetType.COMPANY:
            return await self._enrich_company(context)
        else:
            raise ValueError(f"Unknown target type: {context.target_type}")
    
    async def _enrich_contact(self, context: EnrichmentContext) -> EnrichmentResult:
        data = context.input_data
        email = data.get("email", "")
        
        result = EnrichmentResult(
            provider=self.provider_name,
            confidence_score=0.7,
            sources=["offline_heuristics"],
        )
        
        # Extract name from email if missing
        if not data.get("first_name") or not data.get("last_name"):
            name_parts = self._extract_name_from_email(email)
            if name_parts:
                result.first_name = name_parts[0]
                result.last_name = name_parts[1]
                result.confidence_score = max(result.confidence_score or 0, 0.6)
        
        # Infer title from email domain patterns
        if not data.get("title"):
            title = self._infer_title_from_email(email)
            if title:
                result.title = title
                result.confidence_score = max(result.confidence_score or 0, 0.5)
        
        # Generate likely LinkedIn URL
        if not data.get("linkedin_url") and data.get("first_name") and data.get("last_name"):
            result.linkedin_url = f"https://linkedin.com/in/{data['first_name'].lower()}-{data['last_name'].lower()}"
            result.confidence_score = max(result.confidence_score or 0, 0.4)
        
        # Add notes based on email domain
        if not data.get("notes"):
            domain = email.split("@")[-1] if "@" in email else ""
            if domain:
                company_guess = domain.split(".")[0].title()
                result.notes = f"Likely works at {company_guess} (inferred from email domain)"
                result.confidence_score = max(result.confidence_score or 0, 0.3)
        
        return result
    
    async def _enrich_company(self, context: EnrichmentContext) -> EnrichmentResult:
        data = context.input_data
        domain = data.get("domain", "") or data.get("website", "")
        
        # Extract domain from website if needed
        if not domain and data.get("website"):
            domain = self._extract_domain(data["website"])
        
        result = EnrichmentResult(
            provider=self.provider_name,
            confidence_score=0.7,
            sources=["offline_heuristics"],
        )
        
        # Infer company name from domain (always infer if domain available)
        if domain:
            result.name = self._infer_company_name_from_domain(domain)
            result.confidence_score = max(result.confidence_score or 0, 0.6)
        
        # Always include domain in result if available
        if domain:
            result.domain = domain
        
        # Infer industry from domain TLD/patterns
        if not data.get("industry") and domain:
            result.industry = self._infer_industry_from_domain(domain)
            result.confidence_score = max(result.confidence_score or 0, 0.4)
        
        # Infer size from domain patterns
        if not data.get("size") and domain:
            result.size = self._infer_size_from_domain(domain)
            result.confidence_score = max(result.confidence_score or 0, 0.3)
        
        # Generate likely LinkedIn URL
        if not data.get("linkedin_url") and domain:
            company_slug = domain.split(".")[0].lower()
            result.linkedin_url = f"https://linkedin.com/company/{company_slug}"
            result.confidence_score = max(result.confidence_score or 0, 0.3)
        
        # Generate website if missing
        if not data.get("website") and domain:
            result.website = f"https://{domain}"
        
        return result
    
    def _extract_name_from_email(self, email: str) -> Optional[tuple]:
        """Extract first/last name from email local part."""
        if not email or "@" not in email:
            return None
        local = email.split("@")[0]
        # Common patterns: firstname.lastname, firstname_lastname, firstnamelastname
        for sep in [".", "_", "-"]:
            if sep in local:
                parts = local.split(sep)
                if len(parts) >= 2:
                    return (parts[0].title(), parts[1].title())
        # Try camelCase or just first part
        if len(local) > 3:
            return (local[:len(local)//2].title(), local[len(local)//2:].title())
        return None
    
    def _infer_title_from_email(self, email: str) -> Optional[str]:
        """Infer job title from email patterns."""
        if not email or "@" not in email:
            return None
        local = email.split("@")[0].lower()
        domain = email.split("@")[1].lower()
        
        # Role-based emails
        role_prefixes = {
            "ceo": "Chief Executive Officer",
            "cto": "Chief Technology Officer",
            "cfo": "Chief Financial Officer",
            "coo": "Chief Operating Officer",
            "cmo": "Chief Marketing Officer",
            "vp": "Vice President",
            "director": "Director",
            "manager": "Manager",
            "lead": "Team Lead",
            "engineer": "Engineer",
            "developer": "Developer",
            "architect": "Architect",
            "founder": "Founder",
            "owner": "Owner",
            "president": "President",
            "principal": "Principal Engineer",
            "staff": "Staff Engineer",
            "senior": "Senior Engineer",
            "hr": "Human Resources",
            "recruiting": "Recruiter",
            "sales": "Sales Representative",
            "support": "Support Engineer",
            "info": "General Contact",
            "hello": "General Contact",
            "contact": "General Contact",
        }
        
        for prefix, title in role_prefixes.items():
            if local.startswith(prefix) or local.endswith(prefix):
                return title
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        return url.split("/")[0].split(":")[0]
    
    def _infer_company_name_from_domain(self, domain: str) -> str:
        """Infer company name from domain."""
        name = domain.split(".")[0]
        # Common suffixes to remove
        for suffix in ["inc", "corp", "llc", "ltd", "co", "com", "io", "ai", "tech", "technologies", "systems", "solutions", "software", "labs", "studio", "group", "partners", "ventures", "capital"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name.title()
    
    def _infer_industry_from_domain(self, domain: str) -> Optional[str]:
        """Infer industry from domain patterns."""
        tld = domain.split(".")[-1].lower()
        name = domain.split(".")[0].lower()
        
        tld_industries = {
            "io": "Technology",
            "ai": "Artificial Intelligence",
            "tech": "Technology",
            "dev": "Software Development",
            "app": "Software",
            "cloud": "Cloud Computing",
            "data": "Data Analytics",
            "finance": "Financial Services",
            "bank": "Banking",
            "health": "Healthcare",
            "med": "Medical",
            "bio": "Biotechnology",
            "edu": "Education",
            "gov": "Government",
            "org": "Non-profit",
        }
        
        if tld in tld_industries:
            return tld_industries[tld]
        
        # Keyword-based inference
        keywords = {
            "fintech": "Financial Technology",
            "healthtech": "Health Technology",
            "edtech": "Education Technology",
            "proptech": "Property Technology",
            "insurtech": "Insurance Technology",
            "regtech": "Regulatory Technology",
            "legaltech": "Legal Technology",
            "martech": "Marketing Technology",
            "hrtech": "HR Technology",
            "saas": "Software as a Service",
            "ai": "Artificial Intelligence",
            "ml": "Machine Learning",
            "crypto": "Cryptocurrency",
            "blockchain": "Blockchain",
            "web3": "Web3",
            "cloud": "Cloud Computing",
            "security": "Cybersecurity",
            "devops": "DevOps",
        }
        
        for kw, industry in keywords.items():
            if kw in name:
                return industry
        return None
    
    def _infer_size_from_domain(self, domain: str) -> Optional[str]:
        """Infer company size from domain patterns (very rough heuristic)."""
        name = domain.split(".")[0].lower()
        
        # Startup indicators
        if any(kw in name for kw in ["labs", "studio", "ventures", "incubator", "accelerator", "seed", "pre-seed"]):
            return "1-10"
        # Enterprise indicators
        if any(kw in name for kw in ["corp", "inc", "enterprises", "global", "international", "group", "holdings"]):
            return "1000+"
        # Mid-market default
        return "50-200"


class LLMEnrichmentProvider(EnrichmentProviderBase):
    """Base class for LLM-based enrichment providers."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    @abstractmethod
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        pass
    
    async def enrich(self, context: EnrichmentContext) -> EnrichmentResult:
        prompt = self._build_prompt(context)
        try:
            response = await self._call_llm(prompt)
            return self._parse_response(response, context)
        except Exception as e:
            # Fallback to offline enrichment on LLM failure
            offline = OfflineEnrichmentProvider()
            result = await offline.enrich(context)
            result.confidence_score = 0.3
            result.sources.append(f"fallback_from_{self.provider_name.value}_error")
            result.notes = f"LLM enrichment failed: {str(e)}; used offline fallback"
            return result
    
    def _build_prompt(self, context: EnrichmentContext) -> str:
        data = context.input_data
        if context.target_type == EnrichmentTargetType.CONTACT:
            return f"""Enrich this contact data with additional information. Return JSON only.
Input: {json.dumps(data)}
Return fields: first_name, last_name, title, linkedin_url, notes, confidence_score (0-1)"""
        else:
            return f"""Enrich this company data with additional information. Return JSON only.
Input: {json.dumps(data)}
Return fields: name, domain, industry, size, annual_revenue, description, address, phone, linkedin_url, website, confidence_score (0-1)"""
    
    def _parse_response(self, response: Dict[str, Any], context: EnrichmentContext) -> EnrichmentResult:
        result = EnrichmentResult(
            provider=self.provider_name,
            confidence_score=response.get("confidence_score", 0.8),
            sources=[self.provider_name.value],
        )
        for key, value in response.items():
            if key != "confidence_score" and value is not None:
                setattr(result, key, value)
        return result


class OpenAICompatibleProvider(LLMEnrichmentProvider):
    """OpenAI-compatible API provider (OpenAI, Azure OpenAI, local models, etc.)."""
    
    @property
    def provider_name(self) -> EnrichmentProvider:
        return EnrichmentProvider.OPENAI_COMPATIBLE
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        url = f"{self.base_url or 'https://api.openai.com/v1'}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a data enrichment assistant. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)


class AnthropicProvider(LLMEnrichmentProvider):
    """Anthropic Claude API provider."""
    
    @property
    def provider_name(self) -> EnrichmentProvider:
        return EnrichmentProvider.ANTHROPIC
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        import httpx
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        url = f"{self.base_url or 'https://api.anthropic.com/v1'}/messages"
        
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "temperature": 0.1,
            "system": "You are a data enrichment assistant. Return valid JSON only.",
            "messages": [{"role": "user", "content": prompt}],
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            return json.loads(content)


class GeminiProvider(LLMEnrichmentProvider):
    """Google Gemini API provider."""
    
    @property
    def provider_name(self) -> EnrichmentProvider:
        return EnrichmentProvider.GEMINI
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        import httpx
        
        url = f"{self.base_url or 'https://generativelanguage.googleapis.com/v1beta'}/models/{self.model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        params = {"key": self.api_key}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, params=params, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content)


class EnrichmentService:
    """Main service for managing enrichment jobs and providers."""
    
    def __init__(self):
        self._providers: Dict[EnrichmentProvider, EnrichmentProviderBase] = {}
        self._register_default_providers()
    
    def _register_default_providers(self):
        self._providers[EnrichmentProvider.OFFLINE] = OfflineEnrichmentProvider()
    
    def register_llm_provider(self, provider: EnrichmentProvider, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        """Register an LLM provider with configuration."""
        if provider == EnrichmentProvider.OPENAI_COMPATIBLE:
            self._providers[provider] = OpenAICompatibleProvider(api_key, base_url, model or settings.LLM_MODEL)
        elif provider == EnrichmentProvider.ANTHROPIC:
            self._providers[provider] = AnthropicProvider(api_key, base_url, model or settings.LLM_MODEL)
        elif provider == EnrichmentProvider.GEMINI:
            self._providers[provider] = GeminiProvider(api_key, base_url, model or settings.LLM_MODEL)
    
    def get_provider(self, provider: EnrichmentProvider) -> Optional[EnrichmentProviderBase]:
        return self._providers.get(provider)
    
    async def create_job(
        self,
        db: AsyncSession,
        target_type: EnrichmentTargetType,
        target_id: int,
        provider: EnrichmentProvider = EnrichmentProvider.OFFLINE,
        config: Optional[Dict[str, Any]] = None,
    ) -> EnrichmentJob:
        """Create a new enrichment job."""
        # Fetch target data for input snapshot
        input_data = await self._get_target_data(db, target_type, target_id)
        
        job = EnrichmentJob(
            target_type=target_type,
            target_id=target_id,
            provider=provider,
            status=EnrichmentStatus.PENDING,
            input_data=json.dumps(input_data) if input_data else None,
            config_snapshot=json.dumps(config) if config else None,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    
    async def _get_target_data(self, db: AsyncSession, target_type: EnrichmentTargetType, target_id: int) -> Optional[Dict[str, Any]]:
        if target_type == EnrichmentTargetType.CONTACT:
            contact = await db.get(Contact, target_id)
            if contact:
                return {
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "title": contact.title,
                    "linkedin_url": contact.linkedin_url,
                    "notes": contact.notes,
                    "company_id": contact.company_id,
                }
        elif target_type == EnrichmentTargetType.COMPANY:
            company = await db.get(Company, target_id)
            if company:
                return {
                    "name": company.name,
                    "domain": company.domain,
                    "industry": company.industry,
                    "size": company.size,
                    "annual_revenue": company.annual_revenue,
                    "description": company.description,
                    "address": company.address,
                    "phone": company.phone,
                    "linkedin_url": company.linkedin_url,
                    "website": company.website,
                }
        return None
    
    async def run_job(self, db: AsyncSession, job_id: int) -> EnrichmentJob:
        """Execute an enrichment job."""
        job = await db.get(EnrichmentJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != EnrichmentStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending (status: {job.status})")
        
        provider_impl = self.get_provider(job.provider)
        if not provider_impl:
            # Auto-register LLM provider from settings if needed
            if job.provider in (EnrichmentProvider.OPENAI_COMPATIBLE, EnrichmentProvider.ANTHROPIC, EnrichmentProvider.GEMINI):
                if settings.LLM_API_KEY:
                    self.register_llm_provider(job.provider, settings.LLM_API_KEY, settings.LLM_BASE_URL, settings.LLM_MODEL)
                    provider_impl = self.get_provider(job.provider)
        
        if not provider_impl:
            raise ValueError(f"Provider {job.provider} not available")
        
        # Update status to running
        job.status = EnrichmentStatus.RUNNING
        job.started_at = datetime.utcnow()
        await db.commit()
        
        try:
            # Prepare context
            input_data = json.loads(job.input_data) if job.input_data else {}
            config = json.loads(job.config_snapshot) if job.config_snapshot else {}
            
            context = EnrichmentContext(
                target_type=job.target_type,
                target_id=job.target_id,
                input_data=input_data,
                config=config,
            )
            
            # Run enrichment
            result = await provider_impl.enrich(context)
            
            # Save result
            job.result_data = json.dumps(result.model_dump(mode="json"))
            job.status = EnrichmentStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = EnrichmentStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job)
        return job
    
    async def apply_enrichment(
        self,
        db: AsyncSession,
        job_id: int,
        apply: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Apply enrichment results to the target entity."""
        job = await db.get(EnrichmentJob, job_id)
        if not job or job.status != EnrichmentStatus.COMPLETED or not job.result_data:
            return None
        
        result_data = json.loads(job.result_data)
        result = EnrichmentResult(**result_data)
        
        if not apply:
            return result.model_dump(mode="json")
        
        if job.target_type == EnrichmentTargetType.CONTACT:
            contact = await db.get(Contact, job.target_id)
            if contact:
                for field, value in result.model_dump(exclude_unset=True, exclude={"confidence_score", "sources", "enriched_at", "provider"}).items():
                    if value is not None and hasattr(contact, field):
                        setattr(contact, field, value)
                await db.commit()
                await db.refresh(contact)
                return {"applied": True, "entity_type": "contact", "entity_id": contact.id}
        
        elif job.target_type == EnrichmentTargetType.COMPANY:
            company = await db.get(Company, job.target_id)
            if company:
                for field, value in result.model_dump(exclude_unset=True, exclude={"confidence_score", "sources", "enriched_at", "provider"}).items():
                    if value is not None and hasattr(company, field):
                        setattr(company, field, value)
                await db.commit()
                await db.refresh(company)
                return {"applied": True, "entity_type": "company", "entity_id": company.id}
        
        return None
    
    async def list_jobs(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[EnrichmentStatus] = None,
        target_type: Optional[EnrichmentTargetType] = None,
        target_id: Optional[int] = None,
    ) -> tuple[List[EnrichmentJob], int]:
        """List enrichment jobs with filters."""
        from sqlalchemy import func
        
        query = select(EnrichmentJob)
        count_query = select(func.count(EnrichmentJob.id))
        
        if status:
            query = query.where(EnrichmentJob.status == status)
            count_query = count_query.where(EnrichmentJob.status == status)
        if target_type:
            query = query.where(EnrichmentJob.target_type == target_type)
            count_query = count_query.where(EnrichmentJob.target_type == target_type)
        if target_id:
            query = query.where(EnrichmentJob.target_id == target_id)
            count_query = count_query.where(EnrichmentJob.target_id == target_id)
        
        total = (await db.execute(count_query)).scalar_one()
        total_pages = (total + page_size - 1) // page_size
        
        query = query.order_by(EnrichmentJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        jobs = (await db.execute(query)).scalars().all()
        
        return list(jobs), total


# Global service instance
enrichment_service = EnrichmentService()

