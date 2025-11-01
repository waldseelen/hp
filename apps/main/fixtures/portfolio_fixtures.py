"""
Portfolio Fixtures for UI Kit Showcase
Provides realistic test data for portfolio components demonstration
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class MockProject:
    """Mock project data for UI Kit demonstrations"""

    id: int
    title: str
    description: str
    status: str  # 'planning', 'development', 'completed', 'archived'
    category: str  # 'web', 'mobile', 'ai', 'cybersecurity', 'blockchain'
    technologies: List[str]
    image_url: str
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    featured: bool = False
    progress_percentage: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_size: int = 1
    client: Optional[str] = None
    views: int = 0
    likes: int = 0

    @property
    def is_active(self):
        return self.status in ["planning", "development"]

    @property
    def is_completed(self):
        return self.status == "completed"


class PortfolioFixtures:
    """
    Centralized fixtures provider for portfolio components
    Used in UI Kit, tests, and documentation
    """

    @staticmethod
    def get_featured_projects() -> List[MockProject]:
        """Returns featured projects for homepage showcase"""
        return [
            MockProject(
                id=1,
                title="AI-Powered Portfolio Optimizer",
                description="Machine learning system that optimizes portfolio content based on user engagement analytics. Uses TensorFlow and Django to deliver personalized content recommendations.",
                status="completed",
                category="ai",
                technologies=["Python", "TensorFlow", "Django", "PostgreSQL", "Redis"],
                image_url="/media/ai_tools/ai-optimizer.jpg",
                github_url="https://github.com/username/ai-optimizer",
                demo_url="https://ai-optimizer-demo.example.com",
                featured=True,
                progress_percentage=100,
                start_date=datetime(2024, 1, 15),
                end_date=datetime(2024, 6, 30),
                team_size=3,
                views=1247,
                likes=89,
            ),
            MockProject(
                id=2,
                title="Cybersecurity Vulnerability Scanner",
                description="Enterprise-grade security scanning tool with real-time threat detection. Identifies OWASP Top 10 vulnerabilities and provides automated remediation suggestions.",
                status="completed",
                category="cybersecurity",
                technologies=["Python", "FastAPI", "React", "Docker", "AWS"],
                image_url="/media/cybersecurity/security-scanner.jpg",
                github_url="https://github.com/username/vuln-scanner",
                demo_url="https://security-scanner-demo.example.com",
                featured=True,
                progress_percentage=100,
                start_date=datetime(2024, 3, 1),
                end_date=datetime(2024, 8, 15),
                team_size=5,
                client="SecureTech Corp",
                views=2156,
                likes=134,
            ),
            MockProject(
                id=3,
                title="Blockchain-Based Supply Chain",
                description="Decentralized supply chain management platform using Ethereum smart contracts. Enables transparent tracking of products from manufacturer to consumer.",
                status="development",
                category="blockchain",
                technologies=["Solidity", "Web3.js", "Node.js", "MongoDB", "IPFS"],
                image_url="/media/tools/blockchain-supply.jpg",
                github_url="https://github.com/username/blockchain-supply",
                featured=True,
                progress_percentage=75,
                start_date=datetime(2024, 7, 1),
                team_size=4,
                client="LogiChain Solutions",
                views=856,
                likes=67,
            ),
        ]

    @staticmethod
    def get_development_projects() -> List[MockProject]:
        """Returns projects currently in development"""
        return [
            MockProject(
                id=4,
                title="Real-Time Chat Application",
                description="WebSocket-based chat platform with end-to-end encryption, file sharing, and video call capabilities.",
                status="development",
                category="web",
                technologies=["Django", "Channels", "WebRTC", "Vue.js", "PostgreSQL"],
                image_url="/media/tools/chat-app.jpg",
                github_url="https://github.com/username/realtime-chat",
                featured=False,
                progress_percentage=60,
                start_date=datetime(2024, 9, 1),
                team_size=2,
                views=423,
                likes=34,
            ),
            MockProject(
                id=5,
                title="Mobile Fitness Tracker",
                description="Cross-platform mobile app for tracking workouts, nutrition, and health metrics with AI-powered recommendations.",
                status="development",
                category="mobile",
                technologies=["React Native", "Firebase", "TensorFlow Lite", "Redux"],
                image_url="/media/tools/fitness-tracker.jpg",
                github_url="https://github.com/username/fitness-tracker",
                featured=False,
                progress_percentage=45,
                start_date=datetime(2024, 10, 1),
                team_size=3,
                views=567,
                likes=45,
            ),
            MockProject(
                id=6,
                title="Cloud Infrastructure Dashboard",
                description="Multi-cloud monitoring and management dashboard supporting AWS, Azure, and GCP with cost optimization features.",
                status="development",
                category="web",
                technologies=["React", "Python", "Kubernetes", "Prometheus", "Grafana"],
                image_url="/media/tools/cloud-dashboard.jpg",
                github_url="https://github.com/username/cloud-dashboard",
                featured=False,
                progress_percentage=30,
                start_date=datetime(2024, 11, 1),
                team_size=4,
                client="CloudTech Inc",
                views=289,
                likes=22,
            ),
        ]

    @staticmethod
    def get_completed_projects() -> List[MockProject]:
        """Returns successfully completed projects"""
        return [
            MockProject(
                id=7,
                title="E-Commerce Platform",
                description="Full-featured online shopping platform with payment integration, inventory management, and customer analytics.",
                status="completed",
                category="web",
                technologies=["Django", "Stripe", "PostgreSQL", "Celery", "Redis"],
                image_url="/media/tools/ecommerce.jpg",
                github_url="https://github.com/username/ecommerce-platform",
                demo_url="https://ecommerce-demo.example.com",
                featured=False,
                progress_percentage=100,
                start_date=datetime(2023, 6, 1),
                end_date=datetime(2024, 2, 28),
                team_size=6,
                client="ShopMaster Ltd",
                views=3421,
                likes=256,
            ),
            MockProject(
                id=8,
                title="Data Visualization Dashboard",
                description="Interactive business intelligence dashboard with real-time data visualization and export capabilities.",
                status="completed",
                category="web",
                technologies=["D3.js", "React", "Python", "FastAPI", "PostgreSQL"],
                image_url="/media/tools/data-viz.jpg",
                github_url="https://github.com/username/data-viz-dashboard",
                demo_url="https://data-viz-demo.example.com",
                featured=False,
                progress_percentage=100,
                start_date=datetime(2023, 9, 1),
                end_date=datetime(2024, 4, 15),
                team_size=3,
                client="DataInsights Corp",
                views=1876,
                likes=142,
            ),
        ]

    @staticmethod
    def get_planning_projects() -> List[MockProject]:
        """Returns projects in planning phase"""
        return [
            MockProject(
                id=9,
                title="IoT Smart Home System",
                description="Integrated smart home automation system with voice control, energy monitoring, and security features.",
                status="planning",
                category="mobile",
                technologies=["IoT", "MQTT", "Node.js", "React Native", "MongoDB"],
                image_url="/media/tools/smart-home.jpg",
                featured=False,
                progress_percentage=10,
                start_date=datetime(2025, 1, 1),
                team_size=4,
                views=124,
                likes=18,
            ),
            MockProject(
                id=10,
                title="AI Content Generator",
                description="Advanced AI system for generating blog posts, social media content, and marketing copy using GPT-4.",
                status="planning",
                category="ai",
                technologies=["Python", "OpenAI API", "Django", "React", "PostgreSQL"],
                image_url="/media/ai_tools/content-generator.jpg",
                featured=False,
                progress_percentage=5,
                start_date=datetime(2025, 2, 1),
                team_size=2,
                views=89,
                likes=12,
            ),
        ]

    @staticmethod
    def get_all_projects() -> List[MockProject]:
        """Returns all projects across all statuses"""
        return (
            PortfolioFixtures.get_featured_projects()
            + PortfolioFixtures.get_development_projects()
            + PortfolioFixtures.get_completed_projects()
            + PortfolioFixtures.get_planning_projects()
        )

    @staticmethod
    def get_projects_by_category(category: str) -> List[MockProject]:
        """Returns projects filtered by category"""
        all_projects = PortfolioFixtures.get_all_projects()
        return [p for p in all_projects if p.category == category]

    @staticmethod
    def get_projects_by_status(status: str) -> List[MockProject]:
        """Returns projects filtered by status"""
        all_projects = PortfolioFixtures.get_all_projects()
        return [p for p in all_projects if p.status == status]

    @staticmethod
    def get_project_stats():
        """Returns project statistics for stat cards"""
        all_projects = PortfolioFixtures.get_all_projects()
        return {
            "total": len(all_projects),
            "completed": len([p for p in all_projects if p.status == "completed"]),
            "in_development": len(
                [p for p in all_projects if p.status == "development"]
            ),
            "planning": len([p for p in all_projects if p.status == "planning"]),
            "total_views": sum(p.views for p in all_projects),
            "total_likes": sum(p.likes for p in all_projects),
            "success_rate": round(
                len([p for p in all_projects if p.status == "completed"])
                / len(all_projects)
                * 100
            ),
        }


class CategoryFixtures:
    """Fixtures for project categories"""

    @staticmethod
    def get_all_categories():
        """Returns all available project categories with metadata"""
        return [
            {
                "id": "web",
                "name": "Web Development",
                "icon": "globe",
                "color": "blue",
                "count": len(PortfolioFixtures.get_projects_by_category("web")),
            },
            {
                "id": "mobile",
                "name": "Mobile Apps",
                "icon": "smartphone",
                "color": "purple",
                "count": len(PortfolioFixtures.get_projects_by_category("mobile")),
            },
            {
                "id": "ai",
                "name": "Artificial Intelligence",
                "icon": "brain",
                "color": "green",
                "count": len(PortfolioFixtures.get_projects_by_category("ai")),
            },
            {
                "id": "cybersecurity",
                "name": "Cybersecurity",
                "icon": "shield",
                "color": "red",
                "count": len(
                    PortfolioFixtures.get_projects_by_category("cybersecurity")
                ),
            },
            {
                "id": "blockchain",
                "name": "Blockchain",
                "icon": "link",
                "color": "yellow",
                "count": len(PortfolioFixtures.get_projects_by_category("blockchain")),
            },
        ]
