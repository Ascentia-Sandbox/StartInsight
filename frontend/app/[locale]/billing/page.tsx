'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Loader2, Check, ExternalLink } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchSubscriptionStatus, createCheckoutSession, createPortalSession } from '@/lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Get started with basic features',
    features: [
      '5 insights per day',
      'Basic market analysis',
      'Save up to 10 insights',
      'Email support',
    ],
  },
  {
    id: 'starter',
    name: 'Starter',
    price: '$19',
    period: 'per month',
    description: 'For individual entrepreneurs',
    features: [
      'Unlimited insights',
      'Advanced scoring (8 dimensions)',
      '5 AI research analyses per month',
      'Export to PDF/CSV',
      'Priority support',
    ],
    popular: true,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$49',
    period: 'per month',
    description: 'For serious founders and teams',
    features: [
      'Everything in Starter',
      'Unlimited AI research analyses',
      'Team collaboration (up to 5 members)',
      'Brand asset generator',
      'API access (1,000 calls/month)',
      'Dedicated support',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '$299',
    period: 'per month',
    description: 'For large teams and organizations',
    features: [
      'Everything in Pro',
      'Unlimited team members',
      'Unlimited API access',
      'Custom AI model fine-tuning',
      'Dedicated account manager',
      'SLA guarantee (99.9% uptime)',
      'White-label options',
      'SSO & SAML support',
    ],
    contactSales: true,
  },
];

export default function BillingPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/billing');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch subscription status
  const { data: subscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ['subscription', accessToken],
    queryFn: () => fetchSubscriptionStatus(accessToken!),
    enabled: !!accessToken,
  });

  // Create checkout session mutation
  const checkoutMutation = useMutation({
    mutationFn: (tier: 'starter' | 'pro' | 'enterprise') =>
      createCheckoutSession(accessToken!, {
        tier,
        billing_cycle: 'monthly',
        success_url: `${window.location.origin}/billing?success=true`,
        cancel_url: `${window.location.origin}/billing?canceled=true`,
      }),
    onSuccess: (data) => {
      // Redirect to Stripe checkout
      window.location.href = data.checkout_url;
    },
  });

  // Create portal session mutation
  const portalMutation = useMutation({
    mutationFn: () => createPortalSession(accessToken!, `${window.location.origin}/billing`),
    onSuccess: (data) => {
      window.location.href = data.portal_url;
    },
  });

  if (isCheckingAuth || subscriptionLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header skeleton */}
          <div className="text-center mb-12">
            <Skeleton className="h-9 w-48 mx-auto mb-2" />
            <Skeleton className="h-4 w-72 mx-auto" />
          </div>
          {/* Plan cards skeleton — 4 columns matching the real grid */}
          <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-20 mb-2" />
                  <Skeleton className="h-10 w-24 mb-1" />
                  <Skeleton className="h-4 w-36" />
                </CardHeader>
                <CardContent className="space-y-3">
                  {[...Array(5)].map((_, j) => (
                    <div key={j} className="flex items-center gap-2">
                      <Skeleton className="h-5 w-5 rounded-full shrink-0" />
                      <Skeleton className="h-4 flex-1" />
                    </div>
                  ))}
                </CardContent>
                <CardFooter>
                  <Skeleton className="h-9 w-full" />
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const currentTier = subscription?.tier || 'free';

  const getButtonText = (planId: string) => {
    if (planId === 'enterprise') return 'Contact Sales';
    if (planId === currentTier) return 'Current Plan';
    if (planId === 'free') return 'Downgrade';
    return `Upgrade to ${planId.charAt(0).toUpperCase() + planId.slice(1)}`;
  };

  const handlePlanAction = (planId: string) => {
    if (planId === 'enterprise') {
      window.location.assign('mailto:enterprise@startinsight.ai');
      return;
    }
    if (planId === currentTier) return;
    if (planId === 'free') {
      portalMutation.mutate();
    } else {
      checkoutMutation.mutate(planId as 'starter' | 'pro');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold tracking-tight">Choose Your Plan</h1>
          <p className="text-muted-foreground mt-2">
            Scale your market research with the right plan for you
          </p>
          {subscription && subscription.tier !== 'free' && (
            <div className="mt-4">
              <Button variant="outline" onClick={() => portalMutation.mutate()}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Manage Subscription
              </Button>
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-4">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative ${plan.popular ? 'border-primary shadow-lg' : ''} ${
                plan.id === currentTier ? 'ring-2 ring-primary' : ''
              } ${'contactSales' in plan ? 'border-violet-200 dark:border-violet-900' : ''}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}
              {'contactSales' in plan && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-violet-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Enterprise
                  </span>
                </div>
              )}
              {plan.id === currentTier && (
                <div className="absolute -top-3 right-4">
                  <span className="bg-green-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Current
                  </span>
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <div className="mt-2">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground ml-2">/{plan.period}</span>
                </div>
                <CardDescription className="mt-2">{plan.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <Check className="h-5 w-5 text-green-500 shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                {'contactSales' in plan ? (
                  <Button
                    className="w-full bg-violet-600 hover:bg-violet-700 text-white"
                    onClick={() => handlePlanAction(plan.id)}
                  >
                    Contact Sales
                  </Button>
                ) : (
                  <Button
                    className="w-full"
                    variant={plan.popular && plan.id !== currentTier ? 'default' : 'outline'}
                    disabled={plan.id === currentTier || checkoutMutation.isPending || portalMutation.isPending}
                    onClick={() => handlePlanAction(plan.id)}
                  >
                    {(checkoutMutation.isPending || portalMutation.isPending) && plan.id !== currentTier ? (
                      <Loader2 className="animate-spin h-4 w-4 mr-2" />
                    ) : null}
                    {getButtonText(plan.id)}
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
          <div className="grid gap-4 md:grid-cols-2 max-w-4xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Can I cancel anytime?</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Yes, you can cancel your subscription at any time. Your access will continue
                  until the end of your billing period.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">What payment methods do you accept?</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  We accept all major credit cards (Visa, Mastercard, Amex) through our secure
                  payment processor, Stripe.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Can I switch plans later?</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Absolutely! You can upgrade or downgrade your plan at any time. Changes take
                  effect immediately.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Is there a free trial?</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Our Free plan lets you try all basic features. Paid plans come with a 7-day
                  money-back guarantee.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Enterprise CTA */}
        <div className="mt-16 text-center">
          <Card className="max-w-2xl mx-auto bg-muted/50">
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold">Need a custom solution?</h3>
              <p className="text-muted-foreground mt-2">
                For enterprise teams with custom requirements, we offer tailored plans with
                dedicated support, SLAs, and white-label options.
              </p>
              <Link href="mailto:enterprise@startinsight.ai">
                <Button variant="outline" className="mt-4">
                  Contact Sales
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
