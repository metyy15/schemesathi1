"use client";

export default function Header() {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-white/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-6">
      <div className="flex items-center flex-1 max-w-xl">
        <div className="relative w-full flex items-center">
          <span className="material-symbols-outlined absolute left-3 text-outline text-xl pointer-events-none">search</span>
          <input
            className="w-full h-10 pl-10 pr-4 bg-[#f2f4f6] text-on-surface placeholder:text-outline rounded-lg text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#131b2e]/10 transition-all"
            placeholder="Search 2,400+ Central & State schemes, subsidies, scholarships..."
            type="search"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center bg-[#f2f4f6] p-1 rounded-lg gap-1">
          <button className="px-2 py-1 rounded bg-white text-xs font-semibold shadow-sm">English</button>
          <button className="px-2 py-1 rounded text-xs text-on-surface-variant hover:text-on-surface">हिंदी</button>
        </div>
        <button className="relative p-2 rounded-lg text-on-surface-variant hover:bg-[#e6e8ea] hover:text-on-surface">
          <span className="material-symbols-outlined text-xl">notifications</span>
          <span className="absolute top-1.5 right-1.5 flex h-2 w-2 rounded-full bg-error"></span>
        </button>
        <div className="flex items-center gap-2 pl-4 border-l border-[#e6e8ea]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-semibold">
            HS
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-sm font-medium leading-tight">Harshvardhan S.</span>
            <span className="text-xs text-on-surface-variant">Karnataka / General</span>
          </div>
        </div>
      </div>
    </header>
  );
}
