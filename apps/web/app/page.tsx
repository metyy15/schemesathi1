"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Dashboard from "@/components/Dashboard";

export default function Home() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="pl-72">
        <Header />
        <main className="pt-16">
          {activeTab === "overview" && <Dashboard />}
          {activeTab !== "overview" && (
            <div className="max-w-[1440px] mx-auto px-6 py-8">
              <div className="bg-surface-container-lowest rounded-xl p-8 shadow-sm">
                <h1 className="text-2xl font-bold mb-4 capitalize">{activeTab.replace(/-/g, ' ')}</h1>
                <p className="text-on-surface-variant">This section is under development. Core functionality is available in Overview.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
