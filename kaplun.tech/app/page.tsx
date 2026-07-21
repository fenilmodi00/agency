"use client";

import { useState } from "react";
import { WaitlistModal } from "./components/WaitlistModal";
import { Navbar } from "./components/Navbar";

const metrics = [
  { value: "8,000+", label: "Creators Sourced" },
  { value: "500+", label: "Campaigns Launched" },
  { value: "68%", label: "Avg. CTR Improvement" },
  { value: "< 24h", label: "Time to First Creators Live" },
];

const services = [
  {
    title: "Influencer Sourcing",
    desc: "AI-driven discovery across Instagram & TikTok. Our engine matches creators to your brand by audience demographics, content style, engagement rates, and historical performance. Vetted shortlists in 24 hours, not weeks.",
    gradient: "var(--clay-brand-pink)",
    color: "var(--clay-on-primary)",
    cls: "kaplun-card",
  },
  {
    title: "Seeding & Affiliates",
    desc: "Done-for-you product gifting and affiliate programme management. We handle sourcing, logistics, posting, rights, and payouts end-to-end — so your team stays focused on strategy.",
    gradient: "var(--clay-brand-teal)",
    color: "var(--clay-on-primary)",
    cls: "kaplun-card",
  },
  {
    title: "Organic Content",
    desc: "Ongoing paid creator posts that build a renewable engine of high-quality content for your owned and earned channels. All with full usage rights for paid amplification.",
    gradient: "var(--clay-brand-lavender)",
    color: "var(--clay-ink)",
    cls: "kaplun-card",
  },
  {
    title: "Creator Ads",
    desc: "Whitelisted creator partnership ads on Meta and TikTok. Ad-ready creative your paid team can plug straight in — no production delays, no rights ambiguity.",
    gradient: "var(--clay-brand-peach)",
    color: "var(--clay-ink)",
    cls: "kaplun-card",
  },
];

const howItWorks = [
  {
    step: "01",
    title: "Source",
    desc: "AI plus a human strategist surface the creators most likely to perform for your brand. Vetted shortlists delivered in 24 hours.",
    day: "Day 1–3",
  },
  {
    step: "02",
    title: "Activate",
    desc: "We send product, sign contracts, and onboard every creator to your affiliate platform — automatically. Your team reviews and approves from one dashboard.",
    day: "Day 4–10",
  },
  {
    step: "03",
    title: "Amplify",
    desc: "Ad-ready whitelisted creative lands in your paid-media pipeline. Run it as-is or A/B test — every asset comes with full usage rights and performance data.",
    day: "Ongoing",
  },
];

const testimonials = [
  {
    quote: "Working with Kaplun felt like hiring an entire influencer marketing team — we supplied the brief, they executed a 360° campaign across hundreds of creators.",
    name: "Freddie Scheckter",
    role: "Chief of Staff",
    brand: "Skin+Me",
    metric: "4.5×",
    metricLabel: "Increase in Signups",
  },
  {
    quote: "Kaplun took over the heavy lifting and manual workflows, freeing us up to focus on strategy — and delivered a 175% increase in revenue in 2 months.",
    name: "Bríd McNulty",
    role: "Global Influencer Channel Lead",
    brand: "Fussy",
    metric: "+175%",
    metricLabel: "Revenue in 2 Months",
  },
];

export default function Home() {
  const [waitlistOpen, setWaitlistOpen] = useState(false);

  return (
    <main style={{ background: "var(--clay-canvas)", minHeight: "100vh" }}>
      {/* ═══ CAPSULE NAV ═══ */}
      <Navbar onOpenWaitlist={() => setWaitlistOpen(true)} />

      {/* ═══ HERO ═══ */}
      <section
        className="kaplun-hero-section kaplun-reveal"
        style={{ padding: "var(--clay-spacing-section) var(--clay-spacing-lg)", maxWidth: 1280, margin: "0 auto" }}
      >
        <div className="kaplun-hero-grid">
          <div>
            <p
              style={{
                fontSize: "var(--clay-caption-uppercase)",
                fontWeight: 600,
                letterSpacing: "1.5px",
                textTransform: "uppercase",
                color: "var(--clay-muted)",
                marginBottom: "var(--clay-spacing-md)",
              }}
            >
              AI-Native Influencer Partner
            </p>
            <h1
              className="kaplun-hero-title"
              style={{
                fontSize: "var(--clay-display-xl)",
                lineHeight: 1.0,
                letterSpacing: "-2.5px",
                fontWeight: 500,
                fontFamily: '"Inter", sans-serif',
                color: "var(--clay-ink)",
                marginBottom: "var(--clay-spacing-lg)",
              }}
            >
              The AI Creator-Led<br />
              Growth Partner
            </h1>
            <p
              style={{
                fontSize: "var(--clay-body-md)",
                color: "var(--clay-body)",
                marginBottom: "var(--clay-spacing-xl)",
                maxWidth: 480,
                lineHeight: 1.6,
              }}
            >
              We pair the best AI for creator marketing with a senior in-house team — so you can ship campaigns that move the
              needle. Sourcing, seeding, affiliates, and creator ads, end-to-end.
            </p>
            <div style={{ display: "flex", gap: "var(--clay-spacing-md)", alignItems: "center", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => setWaitlistOpen(true)}
                className="kaplun-btn"
                style={{
                  background: "var(--clay-primary)",
                  color: "var(--clay-on-primary)",
                  height: 44,
                  padding: "12px 20px",
                  borderRadius: "var(--clay-rounded-md)",
                  fontSize: "var(--clay-button)",
                  fontWeight: 600,
                  fontFamily: '"Inter", sans-serif',
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Get Early Access
              </button>
              <a href="#services" className="kaplun-btn-outline" style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-ink)", fontWeight: 500 }}>
                See our work →
              </a>
            </div>
          </div>

          {/* Illustration */}
          <div className="kaplun-illustration kaplun-card" style={{
            background: "var(--clay-surface-soft)",
            borderRadius: "var(--clay-rounded-xl)",
            padding: "var(--clay-spacing-xl)",
            position: "relative",
            overflow: "hidden",
          }}>
            <div className="kaplun-blob" style={{ position: "absolute", width: 200, height: 200, borderRadius: "50%", background: "radial-gradient(circle, var(--clay-brand-pink) 0%, transparent 70%)", top: 40, right: 60, opacity: 0.8 }} />
            <div className="kaplun-blob" style={{ position: "absolute", width: 160, height: 160, borderRadius: "50%", background: "radial-gradient(circle, var(--clay-brand-teal) 0%, transparent 70%)", bottom: 60, left: 40, opacity: 0.8 }} />
            <div className="kaplun-blob" style={{ position: "absolute", width: 140, height: 140, borderRadius: "50%", background: "radial-gradient(circle, var(--clay-brand-lavender) 0%, transparent 70%)", top: 120, left: 140, opacity: 0.8 }} />
            <div className="kaplun-blob" style={{ position: "absolute", width: 180, height: 180, borderRadius: "50%", background: "radial-gradient(circle, var(--clay-brand-peach) 0%, transparent 70%)", bottom: 140, right: 80, opacity: 0.6 }} />
          </div>
        </div>
      </section>

      {/* ═══ METRICS BAND ═══ */}
      <section className="kaplun-reveal kaplun-reveal-delay-1" style={{ padding: "0 var(--clay-spacing-lg) var(--clay-spacing-section)", maxWidth: 1280, margin: "0 auto" }}>
        <div className="kaplun-metrics-grid" style={{
          background: "var(--clay-surface-soft)",
          borderRadius: "var(--clay-rounded-xl)",
          padding: "var(--clay-spacing-2xl) var(--clay-spacing-xl)",
        }}>
          {metrics.map((m) => (
            <div key={m.label}>
              <p style={{ fontSize: "var(--clay-display-md)", fontWeight: 600, color: "var(--clay-ink)", margin: 0 }}>{m.value}</p>
              <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", margin: "var(--clay-spacing-xs) 0 0" }}>{m.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ SERVICES ═══ */}
      <section id="services" className="kaplun-reveal" style={{ padding: "var(--clay-spacing-section) var(--clay-spacing-lg)", maxWidth: 1280, margin: "0 auto" }}>
        <p className="kaplun-reveal" style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: "var(--clay-muted)", marginBottom: "var(--clay-spacing-sm)" }}>
          What We Do
        </p>
        <h2 className="kaplun-reveal kaplun-reveal-delay-1" style={{ fontSize: "var(--clay-display-lg)", fontWeight: 500, letterSpacing: "-2px", color: "var(--clay-ink)", lineHeight: 1.05, marginBottom: "var(--clay-spacing-2xl)", maxWidth: 640 }}>
          Your Creator Engine,<br />
          Managed End-to-End.
        </h2>
        <div className="kaplun-cards-grid">
          {services.map((s) => (
            <div key={s.title} className={s.cls} style={{ background: s.gradient, borderRadius: "var(--clay-rounded-xl)", padding: "var(--clay-spacing-xl)", color: s.color, display: "flex", flexDirection: "column" }}>
              <span style={{ display: "inline-block", fontSize: "var(--clay-caption-uppercase)", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", opacity: 0.7, marginBottom: "var(--clay-spacing-sm)" }}>
                {services.indexOf(s) + 1 < 10 ? `0${services.indexOf(s) + 1}` : services.indexOf(s) + 1}
              </span>
              <h3 style={{ fontSize: "var(--clay-title-md)", fontWeight: 600, marginBottom: "var(--clay-spacing-xs)" }}>{s.title}</h3>
              <p style={{ fontSize: "var(--clay-body-sm)", opacity: 0.9, lineHeight: 1.6 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="kaplun-reveal kaplun-reveal-delay-2" style={{ padding: "var(--clay-spacing-section) var(--clay-spacing-lg)", maxWidth: 1280, margin: "0 auto" }}>
        <p className="kaplun-reveal" style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: "var(--clay-muted)", marginBottom: "var(--clay-spacing-sm)" }}>
          How It Works
        </p>
        <h2 className="kaplun-reveal kaplun-reveal-delay-1" style={{ fontSize: "var(--clay-display-lg)", fontWeight: 500, letterSpacing: "-2px", color: "var(--clay-ink)", lineHeight: 1.05, marginBottom: "var(--clay-spacing-2xl)" }}>
          Source. Activate.<br />
          Amplify.
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--clay-spacing-xl)" }}>
          {howItWorks.map((h) => (
            <div key={h.step} className="kaplun-steps-grid kaplun-card" style={{ padding: "var(--clay-spacing-xl)", background: "var(--clay-surface-soft)", borderRadius: "var(--clay-rounded-xl)" }}>
              <span className="kaplun-steps-number" style={{ fontSize: "var(--clay-display-sm)", fontWeight: 600, color: "var(--clay-ink)", opacity: 0.2, lineHeight: 1 }}>
                {h.step}
              </span>
              <div>
                <h3 style={{ fontSize: "var(--clay-title-md)", fontWeight: 600, color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-xs)" }}>{h.title}</h3>
                <p style={{ fontSize: "var(--clay-body-md)", color: "var(--clay-body)", lineHeight: 1.6, margin: 0 }}>{h.desc}</p>
              </div>
              <span className="kaplun-steps-day" style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", whiteSpace: "nowrap", paddingTop: 2 }}>
                {h.day}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ TESTIMONIALS ═══ */}
      <section id="results" className="kaplun-reveal" style={{ padding: "var(--clay-spacing-section) var(--clay-spacing-lg)", maxWidth: 1280, margin: "0 auto" }}>
        <p className="kaplun-reveal" style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: "var(--clay-muted)", marginBottom: "var(--clay-spacing-sm)" }}>
          Results
        </p>
        <h2 className="kaplun-reveal kaplun-reveal-delay-1" style={{ fontSize: "var(--clay-display-lg)", fontWeight: 500, letterSpacing: "-2px", color: "var(--clay-ink)", lineHeight: 1.05, marginBottom: "var(--clay-spacing-2xl)" }}>
          What Our Customers Say.
        </h2>
        <div className="kaplun-testimonials-grid">
          {testimonials.map((t, i) => (
            <div key={t.name} className={`kaplun-card ${i === 0 ? "kaplun-reveal" : "kaplun-reveal kaplun-reveal-delay-1"}`} style={{ background: "var(--clay-surface-soft)", borderRadius: "var(--clay-rounded-xl)", padding: "var(--clay-spacing-xl)", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: "var(--clay-display-sm)", fontWeight: 600, color: "var(--clay-brand-pink)", marginBottom: "var(--clay-spacing-md)" }}>
                  {t.metric}
                  <span style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", fontWeight: 400, marginLeft: 8 }}>{t.metricLabel}</span>
                </div>
                <blockquote style={{ fontSize: "var(--clay-body-md)", color: "var(--clay-body)", lineHeight: 1.7, fontStyle: "italic", margin: 0 }}>
                  &ldquo;{t.quote}&rdquo;
                </blockquote>
              </div>
              <div style={{ marginTop: "var(--clay-spacing-lg)" }}>
                <p style={{ fontSize: "var(--clay-body-sm)", fontWeight: 600, color: "var(--clay-ink)", margin: 0 }}>{t.name}</p>
                <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", margin: "2px 0 0" }}>{t.role} · {t.brand}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ PLATFORM ═══ */}
      <section className="kaplun-reveal" style={{ padding: "var(--clay-spacing-section) var(--clay-spacing-lg)", maxWidth: 1280, margin: "0 auto" }}>
        <div className="kaplun-cards-grid">
          <div className="kaplun-card-dark" style={{ background: "var(--clay-primary)", borderRadius: "var(--clay-rounded-xl)", padding: "var(--clay-spacing-xl)", color: "var(--clay-on-primary)", transition: "all 0.35s cubic-bezier(0.22, 1, 0.36, 1)" }}>
            <span style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", opacity: 0.5 }}>Platform</span>
            <h3 style={{ fontSize: "var(--clay-title-lg)", fontWeight: 600, margin: "var(--clay-spacing-sm) 0 var(--clay-spacing-xs)" }}>Mission Control</h3>
            <p style={{ fontSize: "var(--clay-body-sm)", opacity: 0.8, lineHeight: 1.6 }}>See every post. Pick the winners. Stay ahead. All creator content lands in one place — review, approve, and whitelist without spreadsheets.</p>
          </div>
          <div className="kaplun-card" style={{ background: "var(--clay-surface-soft)", borderRadius: "var(--clay-rounded-xl)", padding: "var(--clay-spacing-xl)", color: "var(--clay-ink)" }}>
            <span style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", color: "var(--clay-muted)" }}>Affiliates</span>
            <h3 style={{ fontSize: "var(--clay-title-lg)", fontWeight: 600, margin: "var(--clay-spacing-sm) 0 var(--clay-spacing-xs)" }}>Built-In Affiliate Platform</h3>
            <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-body)", lineHeight: 1.6 }}>Track every sale to the creator behind it. Unique codes, attributed sales, automated payouts. Zero spreadsheets.</p>
          </div>
          <div className="kaplun-card" style={{ background: "var(--clay-brand-lavender)", borderRadius: "var(--clay-rounded-xl)", padding: "var(--clay-spacing-xl)", color: "var(--clay-ink)" }}>
            <span style={{ fontSize: "var(--clay-caption-uppercase)", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", opacity: 0.6 }}>Tuned Per Category</span>
            <h3 style={{ fontSize: "var(--clay-title-lg)", fontWeight: 600, margin: "var(--clay-spacing-sm) 0 var(--clay-spacing-xs)" }}>Built for DTC Brands</h3>
            <p style={{ fontSize: "var(--clay-body-sm)", opacity: 0.85, lineHeight: 1.6 }}>Every category has its own creator playbook. We tune the engine — sourcing, seeding, affiliates, and ads — to the way your industry wins.</p>
          </div>
        </div>
      </section>

      {/* ═══ CLOSING CTA ═══ */}
      <section style={{ padding: "0 var(--clay-spacing-lg) var(--clay-spacing-section)", maxWidth: 1280, margin: "0 auto" }}>
        <div className="kaplun-cta-band kaplun-reveal" style={{ background: "var(--clay-surface-soft)", borderRadius: "var(--clay-rounded-xl)", padding: "80px var(--clay-spacing-xl)", textAlign: "center" }}>
          <h2 className="kaplun-reveal" style={{ fontSize: "var(--clay-display-md)", fontWeight: 500, letterSpacing: "-1px", color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-md)" }}>
            Ready to Ship Campaigns That Move the Needle?
          </h2>
          <p className="kaplun-reveal kaplun-reveal-delay-1" style={{ fontSize: "var(--clay-body-md)", color: "var(--clay-body)", marginBottom: "var(--clay-spacing-xl)", maxWidth: 480, margin: "0 auto var(--clay-spacing-xl)" }}>
            Join the waitlist for early access. Launch campaigns in days, not weeks.
          </p>
          <button
            type="button"
            onClick={() => setWaitlistOpen(true)}
            className="kaplun-btn"
            style={{
              background: "var(--clay-primary)",
              color: "var(--clay-on-primary)",
              height: 44,
              padding: "12px 20px",
              borderRadius: "var(--clay-rounded-md)",
              fontSize: "var(--clay-button)",
              fontWeight: 600,
              fontFamily: '"Inter", sans-serif',
              border: "none",
              cursor: "pointer",
            }}
          >
            Join the Waitlist
          </button>
          <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted-soft)", marginTop: "var(--clay-spacing-md)" }}>No spam, unsubscribe anytime.</p>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer style={{ background: "var(--clay-surface-soft)", padding: "60px var(--clay-spacing-lg) var(--clay-spacing-xl)" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div className="kaplun-footer-container">
            <div className="kaplun-footer-brand">
              <h4 style={{ fontSize: "var(--clay-title-lg)", fontWeight: 700, color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-xs)" }}>Kaplun</h4>
              <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", maxWidth: 320, lineHeight: 1.6 }}>
                The AI creator-led growth partner. We pair AI automation with a senior in-house team to ship influencer campaigns that move the needle.
              </p>
            </div>
            
            <div className="kaplun-footer-cols-grid">
              <div>
                <h5 style={{ fontSize: "var(--clay-body-sm)", fontWeight: 600, color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-sm)" }}>Services</h5>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {["Influencer Sourcing", "Seeding & Affiliates", "Organic Content", "Creator Ads"].map((item) => (
                    <li key={item} style={{ marginBottom: "var(--clay-spacing-xs)" }}>
                      <a href="#services" style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", textDecoration: "none" }}>{item}</a>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h5 style={{ fontSize: "var(--clay-body-sm)", fontWeight: 600, color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-sm)" }}>Company</h5>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {["About", "Blog", "Contact"].map((item) => (
                    <li key={item} style={{ marginBottom: "var(--clay-spacing-xs)" }}>
                      <a href={`#${item.toLowerCase()}`} style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", textDecoration: "none" }}>{item}</a>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h5 style={{ fontSize: "var(--clay-body-sm)", fontWeight: 600, color: "var(--clay-ink)", marginBottom: "var(--clay-spacing-sm)" }}>Legal</h5>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {["Privacy", "Terms"].map((item) => (
                    <li key={item} style={{ marginBottom: "var(--clay-spacing-xs)" }}>
                      <a href={`#${item.toLowerCase()}`} style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted)", textDecoration: "none" }}>{item}</a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          <p style={{ fontSize: "var(--clay-body-sm)", color: "var(--clay-muted-soft)", borderTop: "1px solid var(--clay-hairline)", paddingTop: "var(--clay-spacing-lg)", marginTop: "var(--clay-spacing-xl)" }}>
            © 2026 Kaplun. All rights reserved.
          </p>
        </div>
      </footer>

      <WaitlistModal open={waitlistOpen} onClose={() => setWaitlistOpen(false)} />
    </main>
  );
}
