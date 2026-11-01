"use client";

export default function Dashboard() {
  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8 flex flex-col gap-8">
      {/* Welcome Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div className="flex flex-col max-w-3xl">
          <div className="inline-flex items-center gap-1.5 self-start px-2.5 py-1 rounded-full bg-[#e6e8ea] text-on-surface-variant text-xs mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#339471] animate-ping"></span>
            <span>DPI Sync Engine v4.2 • Gazette Polling Active</span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold text-on-surface tracking-tight font-['Plus_Jakarta_Sans']">
            Namaste, Harsh!
          </h1>
          <p className="text-lg text-on-surface-variant mt-1">
            Let's discover government benefits you're eligible for today. Your profile was last matched 24 minutes ago with Central and Karnataka state gazettes.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-xl shadow-sm self-start lg:self-auto">
          <div className="w-8 h-8 rounded-lg bg-[#eceef0] flex items-center justify-center">
            <span className="material-symbols-outlined text-lg">sync</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-outline">Live Repository State</span>
            <span className="text-sm font-medium">Synced with NSP & AgriStack: Today, 10:42 AM</span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard title="Eligible Schemes" value="14 Schemes" badge="+3 new this mo" subtext="8 Central • 6 Karnataka State" icon="check_circle" color="green" />
        <MetricCard title="Applications In Progress" value="2 Active" subtext="1 Under DBT Review • 1 Ready for Submission" icon="assignment" color="orange" />
        <MetricCard title="Upcoming Deadlines" value="3 Days Left" subtext="Nat. Merit-cum-Means closes Oct 31" icon="schedule" color="red" />
        <MetricCard title="Documents Verified" value="3 / 4 Ready" subtext="1 document needs renewal" icon="verified_user" color="blue" />
      </div>

      {/* Schemes */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Top Matching Schemes For You</h2>
          <button className="text-sm font-medium text-secondary hover:underline flex items-center gap-1">
            View All <span className="material-symbols-outlined text-sm">arrow_forward</span>
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <SchemeCard
            scope="Central Government"
            ministry="Ministry of Education"
            title="National Scholarship for Higher Education (NSP)"
            benefit="₹20,000 - ₹1,25,000 per annum"
            match="96%"
            status="likely eligible"
            deadline="Oct 31, 2024"
          />
          <SchemeCard
            scope="Karnataka State"
            ministry="Dept. of Backward Classes Welfare"
            title="Post-Matric Scholarship for OBC Students"
            benefit="₹1,500 - ₹11,500 per annum"
            match="94%"
            status="likely eligible"
            deadline="Nov 15, 2024"
          />
          <SchemeCard
            scope="Central Government"
            ministry="Ministry of MSME"
            title="PM Vishwakarma Toolkit & Credit Incentive"
            benefit="₹15k Voucher + 5% Subsidized Loan"
            match="88%"
            status="needs info"
            deadline="Rolling"
          />
        </div>
      </div>

      {/* Disclaimer */}
      <div className="p-4 rounded-xl bg-[#f2f4f6] flex items-start gap-2">
        <span className="material-symbols-outlined text-outline">policy</span>
        <p className="text-sm text-on-surface-variant">
          <strong className="text-on-surface">Demonstration Data Notice:</strong> Real application submission and official approval remain strictly under the sovereign jurisdiction of respective Union and State Ministries. SchemeSathi computes assistive eligibility scores only. <strong>This is not a guarantee of eligibility, approval, or benefit payment.</strong>
        </p>
      </div>
    </div>
  );
}

function MetricCard({ title, value, badge, subtext, icon, color }: any) {
  const colors: any = {
    green: "bg-[#ecfdf5] text-[#047857]",
    orange: "bg-[#fff7ed] text-[#c2410c]",
    red: "bg-[#fef2f2] text-[#dc2626]",
    blue: "bg-[#eff6ff] text-[#2563eb]",
  };
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-on-surface-variant font-medium">{title}</span>
        {badge && <span className="text-xs px-2 py-0.5 rounded-full bg-[#ecfdf5] text-[#047857] font-semibold">{badge}</span>}
        {!badge && <span className={`material-symbols-outlined ${colors[color].split(' ')[1]}`}>{icon}</span>}
      </div>
      <div className="text-2xl font-bold mb-2">{value}</div>
      <p className="text-sm text-on-surface-variant">{subtext}</p>
    </div>
  );
}

function SchemeCard({ scope, ministry, title, benefit, match, status, deadline }: any) {
  const statusColors: any = {
    "likely eligible": "text-[#047857]",
    "needs info": "text-[#c2410c]",
  };
  const statusDots: any = {
    "likely eligible": "bg-[#339471]",
    "needs info": "bg-[#fe702a]",
  };
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <span className="px-2.5 py-1 rounded bg-[#eceef0] text-xs font-semibold text-on-surface-variant">{scope}</span>
        <span className="px-2.5 py-1 rounded-full bg-[#e6e8ea] text-xs font-bold flex items-center gap-1">
          <span className="material-symbols-outlined text-xs">info</span>
          {match} Match
        </span>
      </div>
      <div className="mb-3">
        <span className="text-xs text-outline font-semibold uppercase tracking-wider">{ministry}</span>
        <h3 className="text-lg font-semibold mt-1 line-clamp-2">{title}</h3>
      </div>
      <div className="p-2 rounded-lg bg-[#f2f4f6] mb-4">
        <span className="text-xs text-outline block">Entitlement Benefit</span>
        <span className="text-base font-bold text-secondary">{benefit}</span>
      </div>
      <div className="flex items-center justify-between mb-4 pt-4 border-t border-[#eceef0]">
        <span className="text-sm text-on-surface-variant flex items-center gap-1">
          <span className="material-symbols-outlined text-sm">schedule</span>
          {deadline}
        </span>
        <span className={`text-sm font-semibold flex items-center gap-1 ${statusColors[status]}`}>
          <span className={`w-2 h-2 rounded-full ${statusDots[status]}`}></span>
          {status === "likely eligible" ? "Likely Eligible" : "Needs Minor Info"}
        </span>
      </div>
      <button className={`w-full py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
        status === "likely eligible" 
          ? "bg-[#131b2e] text-white hover:bg-black" 
          : "bg-[#eceef0] hover:bg-[#e6e8ea]"
      }`}>
        <span>{status === "likely eligible" ? "View Details & Apply" : "Review Criteria"}</span>
        <span className="material-symbols-outlined text-sm">arrow_forward</span>
      </button>
    </div>
  );
}
