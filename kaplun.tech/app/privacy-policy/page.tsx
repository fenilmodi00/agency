import type { Metadata } from "next";
import { Navbar } from "../components/Navbar";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "Read the Kaplun privacy policy and learn how we collect, use, retain, and protect user information on our platform.",
  alternates: {
    canonical: "https://kaplun.tech/privacy-policy",
  },
};

const sections = [
  {
    id: "information-collection",
    title: "Information We Collect",
    content: `When you use Kaplun's platform and services, we collect information that you provide directly and information collected automatically through your use of our services.

**Information You Provide:**
- Account registration details (name, email address, company name)
- Payment and billing information
- Profile information for creators (Instagram username, follower counts, engagement data, content categories)
- Brand briefs, campaign details, and creative assets
- Communication preferences and correspondence with our team
- Tax and payout information for creators (bank details, PAN/tax identification)

**Automatically Collected Information:**
- Device information (IP address, browser type, operating system)
- Usage data (pages visited, features used, time spent on platform)
- Log data (access times, referring URLs, error logs)
- Location data (approximate geographic location based on IP address)

**Third-Party Data (including Meta/Facebook Platform Data):**
- Instagram profile data (username, follower count, engagement metrics, content categories) via Instagram API
- TikTok creator data where applicable
- Payment processor transaction data
- Analytics data from Google Analytics and similar services

**Meta/Facebook Platform Data:**
If you connect your Facebook or Instagram account to our platform, we may collect data from Meta's platform as permitted by your permissions, including:
- User ID and profile information
- Instagram account details and content
- Page and audience insights
- Any other data you authorize us to access through Meta's APIs`,
  },
  {
    id: "information-use",
    title: "How We Use Your Information",
    content: `We use the information we collect for the following purposes:

**Service Delivery:**
- Provide, operate, and maintain our AI-powered influencer marketing platform
- Process creator sourcing, matching, and recommendation algorithms
- Manage campaign workflows, contracts, and payments between brands and creators
- Deliver whitelisting services, content rights management, and ad-ready creative assets

**Communication:**
- Communicate with you about your account, campaigns, and platform updates
- Send marketing communications (with your consent where required)
- Respond to your inquiries and provide customer support

**Improvement and Security:**
- Analyze platform usage to improve our services and AI models
- Detect and prevent fraud, abuse, and security incidents
- Comply with legal obligations and enforce our terms

**AI and Machine Learning:**
We use aggregated and anonymized data to train and improve our AI-driven discovery engine, which matches creators to brand objectives based on audience demographics, content style, and engagement rates. Individual user data is not sold to third parties.

**Meta/Facebook Platform Data Usage:**
Any data received from Meta's platform is used solely for the purposes described in our App Dashboard and this Privacy Policy, including:
- Creator discovery and matching
- Campaign performance analysis
- Content rights management
- We do not use Meta data for purposes beyond what is disclosed in our App Dashboard`,
  },
  {
    id: "information-sharing",
    title: "Information Sharing and Disclosure",
    content: `We may share your information in the following circumstances:

**With Platform Participants:**
- When a brand engages a creator through our platform, relevant profile and campaign information is shared between the parties to facilitate the collaboration
- Payment information is shared with payment processors to complete transactions

**With Service Providers:**
We work with third-party service providers who assist in operating our platform, including:
- Cloud hosting providers (infrastructure and data storage)
- Payment processors (transaction handling)
- Analytics providers (usage insights)
- Communication tools (email, notifications)
- Meta/Facebook APIs (creator data access)
- Instagram and TikTok APIs (creator data access)

**For Legal Compliance:**
We may disclose information if required by law, regulation, legal process, or governmental request, or when we believe disclosure is necessary to protect our rights, your safety, or the safety of others.

**Business Transfers:**
In the event of a merger, acquisition, or sale of assets, your information may be transferred as part of that transaction, subject to the same privacy protections.

**We Never:**
- Sell your personal information to third parties for their marketing purposes
- Share your data with competitors
- Use your data for purposes unrelated to our services without your consent
- Use Meta Platform Data for any purpose not disclosed in our App Dashboard`,
  },
  {
    id: "data-retention",
    title: "Data Retention",
    content: `We retain your personal information for as long as your account is active or as needed to provide you with our services. We will also retain your information as necessary to comply with legal obligations, resolve disputes, and enforce our agreements.

When you delete your account, we will remove your personal information from our active systems within 30 days. However, some information may be retained in our backup systems for a reasonable period to ensure data integrity and comply with legal requirements.

Campaign data and content rights records may be retained for the duration specified in your contracts and as required for legal and compliance purposes.

**Meta Platform Data Retention:**
Data received from Meta's platform is retained only for as long as necessary to provide the services for which it was collected, or as required by applicable law.`,
  },
  {
    id: "data-security",
    title: "Data Security",
    content: `We take the security of your information seriously and implement appropriate technical and organizational measures to protect it, including:

- Encryption of data in transit (TLS 1.2 or higher) and at rest
- Regular security assessments and penetration testing
- Access controls and authentication requirements for our systems
- Employee training on data protection and privacy practices
- Incident response procedures for potential data breaches
- Technical and administrative controls to protect data on organizational devices

While we strive to protect your personal information, no method of transmission over the Internet or electronic storage is 100% secure. We cannot guarantee absolute security, but we will promptly notify affected users in the event of a data breach as required by applicable law.

**Meta Data Security Requirements:**
In accordance with Meta's Developer Policies, we maintain appropriate security measures for Platform Data, including encryption at rest and in transit, and regular vulnerability testing.`,
  },
  {
    id: "cookies",
    title: "Cookies and Tracking Technologies",
    content: `We use cookies and similar tracking technologies to enhance your experience on our platform.

**Types of Cookies We Use:**
- **Essential cookies:** Required for platform functionality (authentication, session management)
- **Analytics cookies:** Help us understand how users interact with our platform
- **Marketing cookies:** Used to deliver relevant advertisements and measure campaign effectiveness

**Managing Cookies:**
You can control cookies through your browser settings. Disabling certain cookies may affect platform functionality. Most web browsers allow you to:
- View what cookies are stored
- Delete cookies individually or all at once
- Block third-party cookies
- Accept all cookies
- Receive notifications when cookies are set

**Third-Party Analytics:**
We use Google Analytics and similar services to analyze platform usage. These services may use cookies and collect information about your online activities. You can opt out of Google Analytics by installing the Google Analytics Opt-out Browser Add-on.`,
  },
  {
    id: "your-rights",
    title: "Your Rights and Choices",
    content: `Depending on your location, you may have the following rights regarding your personal information:

**Access and Portability:**
- Request a copy of the personal information we hold about you
- Request that we provide your data in a structured, commonly used, and machine-readable format

**Correction and Updates:**
- Request correction of inaccurate or incomplete personal information
- Update your account information at any time through your account settings

**Deletion:**
- Request deletion of your personal information, subject to certain legal exceptions
- Delete your account through the platform or by contacting us

**Consent Withdrawal:**
- Opt out of marketing communications at any time by clicking "unsubscribe" in emails or adjusting your notification preferences
- Withdraw consent for data processing where consent was the basis for processing

**How to Request Deletion:**
You may request deletion of your personal data by:
1. Emailing us at privacy@kaplun.tech with the subject line "Data Deletion Request"
2. Using the account deletion feature in your account settings
3. Contacting our support team at support@kaplun.tech

We will respond to all deletion requests within 30 days.

**To Exercise Your Rights:**
Contact us at privacy@kaplun.tech with your request. We will respond to verified requests within 30 days.

**For EU/EEA Users:**
If you are located in the European Economic Area, you have additional rights under the General Data Protection Regulation (GDPR), including the right to restrict processing and the right to data portability.`,
  },
  {
    id: "facebook-data-deletion",
    title: "Facebook/Meta Data Deletion Instructions",
    content: `In compliance with Meta's Developer Policies, we provide clear instructions for users to request deletion of their data:

**For Facebook/Instagram Users:**
If you have connected your Facebook or Instagram account to our platform, you may request deletion of your data by:

1. **Through Our Platform:**
   - Log into your Kaplun account
   - Navigate to Account Settings > Connected Accounts
   - Click "Disconnect" next to Facebook/Instagram
   - Select "Delete my data" to request complete deletion

2. **Via Email:**
   - Send an email to privacy@kaplun.tech with:
     - Subject: "Facebook/Instagram Data Deletion Request"
     - Your Facebook/Instagram username or email associated with the account
     - A statement requesting deletion of your Facebook/Instagram data

3. **Through Facebook's App Settings:**
   - Go to your Facebook Settings > Apps and Websites
   - Find "Kaplun" in your connected apps
   - Click "Remove" to revoke access
   - Contact us at privacy@kaplun.tech to request deletion of previously collected data

**What Gets Deleted:**
Upon receiving your deletion request, we will delete:
- Your Facebook/Instagram profile data stored in our systems
- Any audience insights or engagement data derived from your account
- Campaign data associated with your Facebook/Instagram account
- Any other personal data collected through Meta's APIs

**Deletion Timeline:**
We will process your deletion request within 30 days. Some data may be retained in backup systems for up to 90 days for disaster recovery purposes, after which it will be permanently deleted.

**Contact for Deletion Requests:**
Email: privacy@kaplun.tech
Subject Line: "Data Deletion Request"
Response Time: Within 30 days`,
  },
  {
    id: "children-privacy",
    title: "Children's Privacy (COPPA Compliance)",
    content: `Kaplun's services are not directed to individuals under the age of 18. We do not knowingly collect personal information from children under 18.

In compliance with the Children's Online Privacy Protection Act (COPPA):
- We do not knowingly collect personal information from children under 13
- If we become aware that we have collected personal information from a child under 13, we will take steps to delete that information promptly
- If you are a parent or guardian and believe your child under 13 has provided us with personal information, please contact us at privacy@kaplun.tech

For users between 13 and 18 years of age, we require parental or guardian consent before collecting personal information.`,
  },
  {
    id: "international-data",
    title: "International Data Transfers",
    content: `Your information may be transferred to and processed in countries other than your country of residence. These countries may have data protection laws that differ from the laws of your country.

When we transfer data internationally, we ensure appropriate safeguards are in place, including:
- Standard Contractual Clauses (SCCs) approved by the European Commission
- Data processing agreements with our service providers
- Encryption and access controls for data in transit

By using our services, you acknowledge and consent to the transfer of your information to countries outside your country of residence, subject to these safeguards.`,
  },
  {
    id: "third-party-links",
    title: "Third-Party Links and Services",
    content: `Our platform may contain links to third-party websites, services, or applications that are not operated by us. We are not responsible for the privacy practices of these third parties. We encourage you to review the privacy policies of any third-party services you access through our platform.

**Third-Party Services We Use:**
- Meta/Facebook APIs (Instagram creator data access)
- TikTok APIs (creator data access)
- Google Analytics (platform analytics)
- Payment processors (transaction handling)
- Cloud hosting providers (infrastructure)

Each of these services has its own privacy policy governing how they collect and use data.

**Meta Platform Terms:**
When we access data through Meta's platform, we comply with Meta's Platform Terms, Developer Policies, and all applicable terms and policies. For more information, visit https://developers.facebook.com/terms`,
  },
  {
    id: "changes",
    title: "Changes to This Privacy Policy",
    content: `We may update this Privacy Policy from time to time to reflect changes in our practices, technologies, legal requirements, or other factors. We will notify you of any material changes by:
- Posting the updated Privacy Policy on this page
- Updating the "Last Updated" date at the top of this page
- Sending you an email notification for significant changes (if you have an account)

We encourage you to review this Privacy Policy periodically. Your continued use of our services after any changes indicates your acceptance of the updated Privacy Policy.`,
  },
  {
    id: "contact",
    title: "Contact Us",
    content: `If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices, please contact us:

**Email:** privacy@kaplun.tech
**Website:** [kaplun.tech](https://kaplun.tech)

We will respond to your inquiry within 30 days.

**For Data Deletion Requests:**
Email: privacy@kaplun.tech
Subject Line: "Data Deletion Request"

**For EU/EEA Residents:**
You also have the right to lodge a complaint with your local data protection authority if you believe your rights under applicable data protection laws have been violated.`,
  },
];

export default function PrivacyPolicyPage() {
  return (
    <main style={{ background: "var(--clay-canvas)", minHeight: "100vh" }}>
      <Navbar />

      {/* Hero Section */}
      <section
        style={{
          padding: "var(--clay-spacing-section) var(--clay-spacing-lg) var(--clay-spacing-2xl)",
          maxWidth: 1280,
          margin: "0 auto",
          paddingTop: "120px",
        }}
      >
        <p
          style={{
            fontSize: "var(--clay-caption-uppercase)",
            fontWeight: 600,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
            color: "var(--clay-muted)",
            marginBottom: "var(--clay-spacing-sm)",
          }}
        >
          Legal
        </p>
        <h1
          style={{
            fontSize: "var(--clay-display-lg)",
            fontWeight: 500,
            letterSpacing: "-2px",
            color: "var(--clay-ink)",
            lineHeight: 1.05,
            marginBottom: "var(--clay-spacing-md)",
          }}
        >
          Privacy Policy
        </h1>
        <p
          style={{
            fontSize: "var(--clay-body-md)",
            color: "var(--clay-body)",
            maxWidth: 640,
            lineHeight: 1.6,
          }}
        >
          Last updated: July 21, 2026
        </p>
      </section>

      {/* Table of Contents */}
      <section
        style={{
          padding: "0 var(--clay-spacing-lg) var(--clay-spacing-2xl)",
          maxWidth: 1280,
          margin: "0 auto",
        }}
      >
        <div
          style={{
            background: "var(--clay-surface-soft)",
            borderRadius: "var(--clay-rounded-lg)",
            padding: "var(--clay-spacing-xl)",
          }}
        >
          <h2
            style={{
              fontSize: "var(--clay-title-md)",
              fontWeight: 600,
              color: "var(--clay-ink)",
              marginBottom: "var(--clay-spacing-md)",
            }}
          >
            Contents
          </h2>
          <nav>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                gap: "var(--clay-spacing-sm)",
              }}
            >
              {sections.map((section) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    style={{
                      fontSize: "var(--clay-body-sm)",
                      color: "var(--clay-body)",
                      textDecoration: "none",
                    }}
                  >
                    {section.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </section>

      {/* Introduction */}
      <section
        style={{
          padding: "0 var(--clay-spacing-lg) var(--clay-spacing-2xl)",
          maxWidth: 1280,
          margin: "0 auto",
        }}
      >
        <div
          style={{
            background: "var(--clay-surface-card)",
            borderRadius: "var(--clay-rounded-xl)",
            padding: "var(--clay-spacing-xl)",
            border: "1px solid var(--clay-hairline)",
          }}
        >
          <p
            style={{
              fontSize: "var(--clay-body-md)",
              color: "var(--clay-body)",
              lineHeight: 1.7,
              margin: 0,
            }}
          >
            Kaplun ("we," "our," or "us") operates the Kaplun platform and related services
            (collectively, the "Service"). This Privacy Policy explains how we collect, use,
            disclose, and safeguard your information when you use our AI-powered influencer
            marketing platform, website, and related services. This policy also describes your
            rights regarding your personal data and how to exercise them, including the right
            to request deletion of your data.
          </p>
        </div>
      </section>

      {/* Policy Sections */}
      <section
        style={{
          padding: "0 var(--clay-spacing-lg) var(--clay-spacing-section)",
          maxWidth: 1280,
          margin: "0 auto",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--clay-spacing-2xl)" }}>
          {sections.map((section, index) => (
            <div key={section.id} id={section.id}>
              <div
                style={{
                  background:
                    index % 6 === 0
                      ? "var(--clay-brand-pink)"
                      : index % 6 === 1
                        ? "var(--clay-brand-teal)"
                        : index % 6 === 2
                          ? "var(--clay-brand-lavender)"
                          : index % 6 === 3
                            ? "var(--clay-brand-peach)"
                            : index % 6 === 4
                              ? "var(--clay-brand-ochre)"
                              : "var(--clay-surface-soft)",
                  borderRadius: "var(--clay-rounded-xl)",
                  padding: "var(--clay-spacing-xl)",
                  color:
                    index % 6 === 0 || index % 6 === 1
                      ? "var(--clay-on-primary)"
                      : "var(--clay-ink)",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    fontSize: "var(--clay-caption-uppercase)",
                    fontWeight: 700,
                    letterSpacing: "1px",
                    textTransform: "uppercase",
                    opacity: 0.6,
                    marginBottom: "var(--clay-spacing-sm)",
                  }}
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2
                  style={{
                    fontSize: "var(--clay-title-lg)",
                    fontWeight: 600,
                    marginBottom: "var(--clay-spacing-md)",
                  }}
                >
                  {section.title}
                </h2>
                <div
                  style={{
                    fontSize: "var(--clay-body-md)",
                    lineHeight: 1.7,
                    opacity: 0.9,
                    whiteSpace: "pre-line",
                  }}
                >
                  {section.content.split("\n\n").map((paragraph, paraIdx) => {
                    const paraKey = paragraph.slice(0, 30).replace(/[^a-zA-Z0-9]/g, "");
                    const parts = paragraph.split(/(\*\*[^*]+\*\*)/g);
                    return (
                  <p
                    key={`p-${section.id}-${paraKey}`}
                    style={{
                      margin: paraIdx === 0 ? 0 : "var(--clay-spacing-sm) 0 0",
                    }}
                  >
                    {parts.map((part) => {
                      if (part.startsWith("**") && part.endsWith("**")) {
                        return (
                          <strong key={`b-${section.id}-${paraKey}-${part.slice(2, 8)}`}>{part.slice(2, -2)}</strong>
                        );
                      }
                      return part;
                    })}
                  </p>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer
        style={{
          background: "var(--clay-surface-soft)",
          padding: "60px var(--clay-spacing-lg) var(--clay-spacing-xl)",
        }}
      >
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--clay-spacing-md)",
              marginBottom: "var(--clay-spacing-xl)",
            }}
          >
            <div>
              <h4
                style={{
                  fontSize: "var(--clay-title-lg)",
                  fontWeight: 700,
                  color: "var(--clay-ink)",
                  marginBottom: "var(--clay-spacing-xs)",
                }}
              >
                Kaplun
              </h4>
              <p
                style={{
                  fontSize: "var(--clay-body-sm)",
                  color: "var(--clay-muted)",
                  maxWidth: 320,
                  lineHeight: 1.6,
                }}
              >
                The AI creator-led growth partner. We pair AI automation with a senior
                in-house team to ship influencer campaigns that move the needle.
              </p>
            </div>
            <div style={{ display: "flex", gap: "var(--clay-spacing-lg)" }}>
              <a
                href="/"
                style={{
                  fontSize: "var(--clay-body-sm)",
                  color: "var(--clay-body)",
                  textDecoration: "none",
                }}
              >
                Home
              </a>
              <a
                href="/privacy-policy"
                style={{
                  fontSize: "var(--clay-body-sm)",
                  color: "var(--clay-ink)",
                  textDecoration: "none",
                  fontWeight: 600,
                }}
              >
                Privacy Policy
              </a>
            </div>
          </div>
          <div
            style={{
              borderTop: "1px solid var(--clay-hairline)",
              paddingTop: "var(--clay-spacing-lg)",
              textAlign: "center",
            }}
          >
            <p
              style={{
                fontSize: "var(--clay-body-sm)",
                color: "var(--clay-muted-soft)",
              }}
            >
              © 2026 Kaplun. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
