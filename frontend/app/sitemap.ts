import { MetadataRoute } from "next";
import { config } from "@/lib/env";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://startinsight.co";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${BASE_URL}/insights`,
      lastModified: new Date(),
      changeFrequency: "hourly",
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/trends`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/pricing`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/features`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/platform-tour`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/tools`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/success-stories`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/market-insights`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/faq`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/about`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${BASE_URL}/contact`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${BASE_URL}/pulse`,
      lastModified: new Date(),
      changeFrequency: "hourly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/idea-of-the-day`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/founder-fits`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/validate`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/developers`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/reports`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/auth/login`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.4,
    },
    {
      url: `${BASE_URL}/auth/signup`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.4,
    },
  ];

  // Dynamic pages - fetch from API
  let dynamicPages: MetadataRoute.Sitemap = [];

  try {
    const apiUrl = config.apiUrl;

    // Fetch insights
    const insightsRes = await fetch(`${apiUrl}/api/insights?limit=100`, {
      next: { revalidate: 3600 }, // Revalidate every hour
    });
    if (insightsRes.ok) {
      const insightsData = await insightsRes.json();
      const insightPages = (insightsData.insights || []).map(
        (insight: { id: string; slug?: string; updated_at?: string }) => ({
          url: `${BASE_URL}/insights/${insight.slug || insight.id}`,
          lastModified: insight.updated_at ? new Date(insight.updated_at) : new Date(),
          changeFrequency: "weekly" as const,
          priority: 0.6,
        })
      );
      dynamicPages = [...dynamicPages, ...insightPages];
    }

    // Fetch success stories
    const storiesRes = await fetch(`${apiUrl}/api/success-stories?limit=50`, {
      next: { revalidate: 3600 },
    });
    if (storiesRes.ok) {
      const storiesData = await storiesRes.json();
      const storyPages = (storiesData.stories || []).map(
        (story: { id: string; updated_at?: string }) => ({
          url: `${BASE_URL}/success-stories/${story.id}`,
          lastModified: story.updated_at ? new Date(story.updated_at) : new Date(),
          changeFrequency: "monthly" as const,
          priority: 0.6,
        })
      );
      dynamicPages = [...dynamicPages, ...storyPages];
    }

    // Fetch market insights (blog articles)
    const articlesRes = await fetch(`${apiUrl}/api/market-insights?limit=50`, {
      next: { revalidate: 3600 },
    });
    if (articlesRes.ok) {
      const articlesData = await articlesRes.json();
      const articlePages = (articlesData.articles || []).map(
        (article: { slug: string; updated_at?: string }) => ({
          url: `${BASE_URL}/market-insights/${article.slug}`,
          lastModified: article.updated_at ? new Date(article.updated_at) : new Date(),
          changeFrequency: "weekly" as const,
          priority: 0.6,
        })
      );
      dynamicPages = [...dynamicPages, ...articlePages];
    }
  } catch (error) {
    console.error("Failed to fetch dynamic sitemap data:", error);
  }

  return [...staticPages, ...dynamicPages];
}
