"use client";

import { useState, useEffect, useRef } from "react";
import { Logo } from "./Logo";

interface NavbarProps {
  onOpenWaitlist: () => void;
}

export function Navbar({ onOpenWaitlist }: NavbarProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const lastScrollYRef = useRef(0);

  // Scroll visibility & background elevation state
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }

      // Hide on scroll down, show on scroll up
      if (currentScrollY > lastScrollYRef.current && currentScrollY > 80) {
        if (!mobileMenuOpen) {
          setIsVisible(false);
        }
      } else if (currentScrollY < lastScrollYRef.current) {
        setIsVisible(true);
      }

      lastScrollYRef.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [mobileMenuOpen]);

  // Lock body scroll when mobile menu drawer is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  // Auto-close mobile drawer on desktop resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleMobileMenu = (e: React.MouseEvent) => {
    e.stopPropagation();
    setMobileMenuOpen((prev) => !prev);
    setIsVisible(true);
  };

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    setMobileMenuOpen(false);
    if (href.startsWith("#")) {
      e.preventDefault();
      const targetEl = document.querySelector(href);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  return (
    <>
      {/* ═══ CAPSULE NAVBAR HEADER ═══ */}
      <header
        className="kaplun-capsule-wrapper"
        style={{
          transform: isVisible || mobileMenuOpen ? "translateY(0)" : "translateY(-140%)",
          opacity: isVisible || mobileMenuOpen ? 1 : 0,
        }}
      >
        <div className={`kaplun-capsule-bar ${isScrolled ? "scrolled" : "top"}`}>
          {/* Brand Logo */}
          <a
            href="#"
            onClick={(e) => handleNavClick(e, "#")}
            style={{
              fontSize: "20px",
              fontWeight: 700,
              color: "var(--clay-ink)",
              letterSpacing: "-0.5px",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Logo size={26} />
            <span>Kaplun</span>
          </a>

          {/* Desktop Nav Links (Hidden on Mobile via CSS) */}
          <nav className="kaplun-desktop-only" style={{ alignItems: "center", gap: "4px" }}>
            <a
              href="#services"
              onClick={(e) => handleNavClick(e, "#services")}
              className="kaplun-capsule-link"
            >
              Services
            </a>
            <a
              href="#how-it-works"
              onClick={(e) => handleNavClick(e, "#how-it-works")}
              className="kaplun-capsule-link"
            >
              How It Works
            </a>
            <a
              href="#results"
              onClick={(e) => handleNavClick(e, "#results")}
              className="kaplun-capsule-link"
            >
              Results
            </a>
          </nav>

          {/* Desktop CTA Button */}
          <div className="kaplun-desktop-only" style={{ alignItems: "center" }}>
            <button
              type="button"
              onClick={onOpenWaitlist}
              className="kaplun-btn"
              style={{
                background: "var(--clay-primary)",
                color: "var(--clay-on-primary)",
                height: "40px",
                padding: "0 20px",
                borderRadius: "9999px",
                fontSize: "14px",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              Join Waitlist
            </button>
          </div>

          {/* Mobile Hamburger Toggle Button (Hidden on Desktop via CSS) */}
          <div className="kaplun-mobile-only" style={{ alignItems: "center" }}>
            <button
              type="button"
              onClick={toggleMobileMenu}
              className="kaplun-hamburger-btn"
              aria-label="Toggle Navigation Menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                /* Close Icon (X) */
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              ) : (
                /* Hamburger Menu Icon (3 horizontal lines) */
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="4" y1="6" x2="20" y2="6" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="18" x2="20" y2="18" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ═══ MOBILE MENU DRAWER OVERLAY ═══ */}
      {mobileMenuOpen && (
        <div
          className="kaplun-mobile-overlay"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="kaplun-mobile-card"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="kaplun-mobile-card-header">
              <span
                style={{
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "var(--clay-ink)",
                  letterSpacing: "-0.5px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <Logo size={24} />
                <span>Kaplun</span>
              </span>

              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="kaplun-hamburger-btn"
                style={{ width: "36px", height: "36px" }}
                aria-label="Close menu"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Nav Items List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <a
                href="#services"
                onClick={(e) => handleNavClick(e, "#services")}
                className="kaplun-mobile-nav-item"
              >
                <span>Services</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
              <a
                href="#how-it-works"
                onClick={(e) => handleNavClick(e, "#how-it-works")}
                className="kaplun-mobile-nav-item"
              >
                <span>How It Works</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
              <a
                href="#results"
                onClick={(e) => handleNavClick(e, "#results")}
                className="kaplun-mobile-nav-item"
              >
                <span>Results</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
            </div>

            <div style={{ height: "1px", background: "var(--clay-hairline)", margin: "2px 0" }} />

            {/* Mobile CTA Button */}
            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenWaitlist();
              }}
              className="kaplun-btn kaplun-mobile-cta-btn"
            >
              <span>Join Waitlist</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: "6px" }}>
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
