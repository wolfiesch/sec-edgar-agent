import { useState } from 'react';
import { Check, ArrowRight, Zap, Table, Search, GitCompare, Shield, Code, Loader2 } from 'lucide-react';

interface LandingPageProps {
  onEnterApp?: () => void;
}

const FEATURES = [
  {
    icon: Table,
    title: '100% Accurate Tables',
    description: 'Extract income statements, balance sheets, and cash flows with perfect accuracy using Inline XBRL.',
  },
  {
    icon: GitCompare,
    title: 'Multi-Company Compare',
    description: 'Compare financial metrics across 2-5 companies side by side with YoY trends.',
  },
  {
    icon: Search,
    title: 'Semantic Search',
    description: 'Search across filings using natural language. Find risk factors, disclosures, and more.',
  },
  {
    icon: Zap,
    title: 'Change Detection',
    description: 'Identify new, removed, and modified risk factors between annual filings.',
  },
];

const PRICING_TIERS = [
  {
    name: 'Starter',
    price: '$99',
    period: '/month',
    description: 'For individual developers',
    features: ['1,000 API calls/month', '10 companies', 'Email support'],
    cta: 'Join Waitlist',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$249',
    period: '/month',
    description: 'For teams & startups',
    features: [
      '10,000 API calls/month',
      'Unlimited companies',
      'Priority support',
      'Python SDK access',
      'Webhook integrations',
    ],
    cta: 'Join Waitlist',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations',
    features: [
      'Unlimited API calls',
      'Dedicated infrastructure',
      'SLA guarantees',
      'Custom integrations',
      'On-premise option',
    ],
    cta: 'Contact Sales',
    highlighted: false,
  },
];

export function LandingPage({ onEnterApp }: LandingPageProps) {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsSubmitting(true);
    // Simulate API call - replace with actual waitlist endpoint
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSubmitted(true);
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-gray-950 to-emerald-900/20" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent" />

        <div className="relative container mx-auto px-4 py-24 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm mb-8">
            <Shield className="w-4 h-4" />
            SEC EDGAR Data for LLMs
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-emerald-400 to-blue-400">
            100% Accurate
            <br />
            Financial Tables
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            Extract structured financial data from SEC filings. Built for AI applications,
            with perfect accuracy and full citations.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <button
              onClick={onEnterApp}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-lg font-semibold text-lg transition-all flex items-center justify-center gap-2"
            >
              Try Demo
              <ArrowRight className="w-5 h-5" />
            </button>
            <a
              href="#waitlist"
              className="px-8 py-4 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg font-semibold text-lg transition-all"
            >
              Join Waitlist
            </a>
          </div>

          {/* Code snippet */}
          <div className="max-w-2xl mx-auto bg-gray-900 rounded-xl border border-gray-800 p-6 text-left">
            <div className="flex items-center gap-2 mb-4">
              <Code className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-500">Python SDK</span>
            </div>
            <pre className="text-sm overflow-x-auto">
              <code className="text-gray-300">
{`from sec_agent import SecClient

client = SecClient(api_key="your-key")

# Get Apple's income statement
income = client.tables.parse(
    ticker="AAPL",
    form_type="10-K",
    year=2024,
    table="income_statement"
)

print(income.structured)  # Structured JSON data
print(income.citation)    # [AAPL 10-K 2024]`}
              </code>
            </pre>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 border-t border-gray-800">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">
            Built for AI Applications
          </h2>
          <p className="text-gray-400 text-center mb-16 max-w-xl mx-auto">
            Every response includes structured data and citations,
            perfect for RAG pipelines and financial AI agents.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="p-6 bg-gray-900/50 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors"
              >
                <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 border-t border-gray-800">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-400 text-center mb-16 max-w-xl mx-auto">
            Start free during beta. Pay as you grow.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {PRICING_TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`p-6 rounded-xl border transition-all ${
                  tier.highlighted
                    ? 'bg-gradient-to-b from-blue-900/30 to-gray-900 border-blue-500/50 scale-105'
                    : 'bg-gray-900/50 border-gray-800 hover:border-gray-700'
                }`}
              >
                {tier.highlighted && (
                  <div className="text-xs font-semibold text-blue-400 mb-2">MOST POPULAR</div>
                )}
                <h3 className="text-xl font-semibold mb-1">{tier.name}</h3>
                <p className="text-gray-400 text-sm mb-4">{tier.description}</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="text-gray-400">{tier.period}</span>
                </div>
                <ul className="space-y-3 mb-6">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-gray-300">
                      <Check className="w-4 h-4 text-emerald-400" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button
                  className={`w-full py-3 rounded-lg font-medium transition-colors ${
                    tier.highlighted
                      ? 'bg-blue-600 hover:bg-blue-500 text-white'
                      : 'bg-gray-800 hover:bg-gray-700 text-gray-200'
                  }`}
                >
                  {tier.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Waitlist Section */}
      <section id="waitlist" className="py-24 border-t border-gray-800">
        <div className="container mx-auto px-4 max-w-2xl text-center">
          <h2 className="text-3xl font-bold mb-4">
            Get Early Access
          </h2>
          <p className="text-gray-400 mb-8">
            Join the waitlist and get 30% off when we launch.
          </p>

          {submitted ? (
            <div className="p-6 bg-emerald-900/30 border border-emerald-700 rounded-xl">
              <Check className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">You're on the list!</h3>
              <p className="text-gray-400">
                We'll notify you when we launch. Thanks for your interest!
              </p>
            </div>
          ) : (
            <form onSubmit={handleWaitlistSubmit} className="flex gap-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Join Waitlist'
                )}
              </button>
            </form>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-gray-800">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          <p>Built by developers, for developers.</p>
          <p className="mt-2">
            Data sourced from SEC EDGAR. Not affiliated with the SEC.
          </p>
        </div>
      </footer>
    </div>
  );
}
