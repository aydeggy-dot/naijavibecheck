'use client';

/**
 * Settings page
 */

import { useState } from 'react';
import { Settings, Instagram, Clock, Bell, Shield, Database } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useSettings, useUpdateSettings } from '@/hooks/useApi';

export default function SettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const updateMutation = useUpdateSettings();

  const [formData, setFormData] = useState({
    scrape_interval: 30,
    auto_approve_threshold: 80,
    max_posts_per_day: 3,
    enable_notifications: true,
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  return (
    <MainLayout title="Settings">
      <div className="max-w-3xl space-y-6">
        {/* Instagram Account */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-pink-100 p-2">
              <Instagram className="h-5 w-5 text-pink-600" />
            </div>
            <div>
              <CardTitle>Instagram Account</CardTitle>
              <CardDescription>Configure your Instagram publishing account</CardDescription>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                placeholder="@naijavibecheck"
                className="w-full rounded-lg border px-4 py-2 focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Access Token
              </label>
              <input
                type="password"
                placeholder="••••••••••••••••"
                className="w-full rounded-lg border px-4 py-2 focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
              />
              <p className="mt-1 text-xs text-gray-500">
                Used for Instagram Graph API access
              </p>
            </div>
          </div>
        </Card>

        {/* Scraping Settings */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-blue-100 p-2">
              <Clock className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle>Scraping Schedule</CardTitle>
              <CardDescription>Configure how often to scrape celebrity posts</CardDescription>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Scrape Interval (minutes)
              </label>
              <select
                value={formData.scrape_interval}
                onChange={(e) =>
                  setFormData({ ...formData, scrape_interval: Number(e.target.value) })
                }
                className="w-full rounded-lg border px-4 py-2 focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
              >
                <option value={15}>Every 15 minutes</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every hour</option>
                <option value={120}>Every 2 hours</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Posts Per Day
              </label>
              <select
                value={formData.max_posts_per_day}
                onChange={(e) =>
                  setFormData({ ...formData, max_posts_per_day: Number(e.target.value) })
                }
                className="w-full rounded-lg border px-4 py-2 focus:border-[#008751] focus:outline-none focus:ring-1 focus:ring-[#008751]"
              >
                <option value={1}>1 post per day</option>
                <option value={2}>2 posts per day</option>
                <option value={3}>3 posts per day</option>
                <option value={5}>5 posts per day</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Auto-Approval */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-green-100 p-2">
              <Shield className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <CardTitle>Auto-Approval</CardTitle>
              <CardDescription>Configure automatic content approval</CardDescription>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Auto-Approve Threshold
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={50}
                  max={100}
                  value={formData.auto_approve_threshold}
                  onChange={(e) =>
                    setFormData({ ...formData, auto_approve_threshold: Number(e.target.value) })
                  }
                  className="flex-1"
                />
                <span className="text-sm font-medium w-12">
                  {formData.auto_approve_threshold}%
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Content from posts with viral score above this threshold will be auto-approved
              </p>
            </div>
          </div>
        </Card>

        {/* Notifications */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-yellow-100 p-2">
              <Bell className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Configure notification preferences</CardDescription>
            </div>
          </div>

          <div className="space-y-4">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.enable_notifications}
                onChange={(e) =>
                  setFormData({ ...formData, enable_notifications: e.target.checked })
                }
                className="rounded border-gray-300 text-[#008751] focus:ring-[#008751]"
              />
              <span className="text-sm text-gray-700">
                Enable email notifications for viral posts
              </span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                defaultChecked
                className="rounded border-gray-300 text-[#008751] focus:ring-[#008751]"
              />
              <span className="text-sm text-gray-700">
                Notify when content is ready for review
              </span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                defaultChecked
                className="rounded border-gray-300 text-[#008751] focus:ring-[#008751]"
              />
              <span className="text-sm text-gray-700">
                Daily summary email
              </span>
            </label>
          </div>
        </Card>

        {/* Database & System */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-purple-100 p-2">
              <Database className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <CardTitle>System</CardTitle>
              <CardDescription>Database and system management</CardDescription>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button variant="outline" size="sm">
              Clear Cache
            </Button>
            <Button variant="outline" size="sm">
              Export Data
            </Button>
            <Button variant="outline" size="sm">
              View Logs
            </Button>
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button
            onClick={handleSave}
            isLoading={updateMutation.isPending}
          >
            Save Settings
          </Button>
        </div>
      </div>
    </MainLayout>
  );
}
