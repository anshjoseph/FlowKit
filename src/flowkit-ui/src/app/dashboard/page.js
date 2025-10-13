"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box } from "lucide-react";

export default function Dashboard() {
    const pathname = usePathname();

    return (
        <div className="min-h-screen bg-white text-black">
            {/* Enhanced Navigation */}
            <nav className="bg-white border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center space-x-8">
                            {/* Logo/Brand */}
                            <div className="flex-shrink-0">
                                <div className="flex items-center gap-2">
                                    <Box className="w-5 h-5" strokeWidth={2} />
                                    <span className="text-lg font-medium tracking-tight">FlowKit</span>
                                </div>
                            </div>

                            {/* Navigation Links */}
                            <div className="hidden md:flex items-center space-x-1">
                                <NavLink
                                    href="/kv"
                                    currentPath={pathname}
                                    label="Secret Key"
                                />
                                <NavLink
                                    href="/resource"
                                    currentPath={pathname}
                                    label="Resource Monitor"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Mobile Navigation */}
            <div className="md:hidden bg-white border-b border-gray-200">
                <div className="px-4 py-2 flex space-x-4 overflow-x-auto">
                    <MobileNavLink
                        href="/kv"
                        currentPath={pathname}
                        label="Secret Key"
                    />
                    <MobileNavLink
                        href="/resource"
                        currentPath={pathname}
                        label="Resource Monitor"
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                <div className="text-gray-700">
                    <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
                    <p>Select an option from above to continue.</p>
                </div>
            </div>
        </div>
    );
}

// Desktop Navigation Link Component
function NavLink({ href, currentPath, label }) {
    const isActive = currentPath === href;

    return (
        <Link
            href={href}
            className={`
        relative px-3 py-2 text-sm font-medium transition-all duration-200
        ${isActive
                    ? 'text-black'
                    : 'text-gray-600 hover:text-black'
                }
      `}
        >
            {label}
            {isActive && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black"></div>
            )}
        </Link>
    );
}

// Mobile Navigation Link Component
function MobileNavLink({ href, currentPath, label }) {
    const isActive = currentPath === href;

    return (
        <Link
            href={href}
            className={`
        whitespace-nowrap px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
        ${isActive
                    ? 'bg-black text-white'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-black'
                }
      `}
        >
            {label}
        </Link>
    );
}