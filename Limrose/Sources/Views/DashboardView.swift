import SwiftUI

struct DashboardView: View {
    var viewModel: DashboardViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header
                Text("Customer Issue Dashboard")
                    .font(.largeTitle.bold())
                    .padding(.bottom, 4)

                // Stat cards
                HStack(spacing: 16) {
                    StatCardView(
                        value: "\(viewModel.stats.totalIssues)",
                        label: "Total Issues",
                        icon: "exclamationmark.triangle",
                        tint: .orange
                    )
                    StatCardView(
                        value: "\(viewModel.stats.resolvedIssues)",
                        label: "Resolved",
                        icon: "checkmark.circle",
                        tint: .green
                    )
                    StatCardView(
                        value: String(format: "%.1f%%", viewModel.stats.resolutionRate),
                        label: "Resolution Rate",
                        icon: "chart.pie",
                        tint: .blue
                    )
                    StatCardView(
                        value: "\(viewModel.stats.documentedFixes)",
                        label: "Documented Fixes",
                        icon: "doc.text",
                        tint: .purple
                    )
                }

                // Two-column grid: categories + issue types
                HStack(alignment: .top, spacing: 20) {
                    IssueCategoriesSection(categories: viewModel.categories)
                    IssueTypesSection(issueTypes: viewModel.topIssueTypes)
                }

                // Recent issues (full width)
                RecentIssuesSection(issues: viewModel.recentIssues)

                // Footer attribution (AOSL license)
                HStack {
                    Spacer()
                    Text("Powered by Email Pipeline by Alec Meeker and Applequist Inc.")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                    Spacer()
                }
                .padding(.top, 12)
            }
            .padding(24)
        }
    }
}
