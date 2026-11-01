"use client";

import Link from "next/link";

const navItems = [
  { id: "overview", label: "Overview", icon: "space_dashboard", active: true },
  { id: "discover-schemes", label: "Discover Schemes", icon: "travel_explore" },
  { id: "ai-eligibility-checker", label: "AI Eligibility Checker", icon: "psychology" },
  { id: "ai-research-activity", label: "AI Research Activity", icon: "radar", badge: true },
  { id: "eligible-scheme-results", label: "Eligible Scheme Results", icon: "rule" },
  { type: "divider", label: "Citizen Services" },
  { id: "my-applications", label: "My Applications", icon: "assignment" },
  { id: "document-vault", label: "Document Vault", icon: "verified_user", badge: "DigiLocker" },
  { id: "deadline-calendar", label: "Deadline Calendar", icon: "event" },
  { id: "saved-schemes", label: "Saved Schemes", icon: "bookmark" },
  { type: "divider", label: "Account & Compliance" },
  { id: "citizen-profile-and-privacy", label: "Citizen Profile & Privacy", icon: "manage_accounts" },
  { id: "official-disclaimers-and-helpdesk", label: "Disclaimers & Helpdesk", icon: "shield_with_heart" },
];

export default function Sidebar({ activeTab, setActiveTab }: { activeTab: string; setActiveTab: (tab: string) => void }) {
  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-[#f2f4f6] z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="flex flex-col flex-1 overflow-y-auto">
        <div className="h-16 px-6 flex items-center gap-2">
          <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-lg">account_balance</span>
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-on-surface">SchemeSathi</span>
            <span className="text-[10px] text-secondary font-semibold uppercase tracking-wider">GovTech Navigator</span>
          </div>
        </div>
        <div className="px-4 py-2">
          <div className="p-2 rounded-lg bg-[#eceef0] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#339471] animate-pulse"></span>
              <span className="text-xs font-medium">NIC & myScheme Sync</span>
            </div>
            <span className="text-xs font-bold text-[#339471] bg-white px-1.5 py-0.5 rounded">99.98%</span>
          </div>
        </div>
        <nav className="flex flex-col gap-1 px-4 mt-2">
          {navItems.map((item, idx) => {
            if (item.type === "divider") {
              return (
                <div key={idx} className="px-2 pt-4 pb-1 text-[10px] uppercase tracking-wider text-outline">
                  {item.label}
                </div>
              );
            }
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id!)}
                className={`flex items-center gap-2 px-2 py-2 rounded-lg transition-all text-left ${
                  isActive
                    ? "bg-[#131b2e] text-white shadow-sm"
                    : "text-on-surface-variant hover:bg-[#e6e8ea] hover:text-on-surface"
                }`}
              >
                <span className="material-symbols-outlined text-xl">{item.icon}</span>
                <span className="text-sm font-medium flex-1">{item.label}</span>
                {item.badge === true && <span className="w-2 h-2 rounded-full bg-[#fe702a]"></span>}
                {typeof item.badge === "string" && (
                  <span className="text-[10px] font-semibold text-[#339471] bg-[#e0e3e5] px-1.5 py-0.5 rounded">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
      <div className="p-4 m-2 rounded-xl bg-[#e0e3e5] flex flex-col gap-1">
        <div className="flex items-center gap-1.5 text-sm font-medium">
          <span className="material-symbols-outlined text-base text-[#339471]">lock</span>
          <span>256-bit Encrypted</span>
        </div>
        <p className="text-xs text-on-surface-variant leading-relaxed">
          Non-official intermediary complying with Digital Personal Data Protection (DPDP) Act 2023.
        </p>
      </div>
    </aside>
  );
}
