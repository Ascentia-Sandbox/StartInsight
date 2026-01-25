import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const plans = [
  {
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
    cta: 'Current Plan',
    disabled: true,
  },
  {
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
    cta: 'Upgrade to Starter',
    popular: true,
  },
  {
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
    cta: 'Upgrade to Pro',
  },
];

export default async function BillingPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/auth/login');
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold tracking-tight">Choose Your Plan</h1>
          <p className="text-muted-foreground mt-2">
            Scale your market research with the right plan for you
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-3">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative ${plan.popular ? 'border-primary shadow-lg' : ''}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
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
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5 text-green-500 shrink-0"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button
                  className="w-full"
                  variant={plan.popular ? 'default' : 'outline'}
                  disabled={plan.disabled}
                >
                  {plan.cta}
                </Button>
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
              <Button variant="outline" className="mt-4">
                Contact Sales
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
