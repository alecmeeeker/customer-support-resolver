import SwiftUI

struct RecentIssuesSection: View {
    let issues: [CustomerIssue]
    @State private var selectedIssue: CustomerIssue?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Recent Issues", systemImage: "clock")
                .font(.headline)

            if issues.isEmpty {
                SectionPlaceholder(text: "No recent issues")
            } else {
                Table(issues, selection: Binding(
                    get: { selectedIssue?.id },
                    set: { id in selectedIssue = issues.first(where: { $0.id == id }) }
                )) {
                    TableColumn("Date") { issue in
                        Text(formatDate(issue.createdAt))
                            .font(.caption)
                            .monospacedDigit()
                    }
                    .width(130)

                    TableColumn("Type") { issue in
                        Text(issue.issueType ?? "-")
                            .fontWeight(.medium)
                    }
                    .width(min: 100)

                    TableColumn("Summary") { issue in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(issue.issueSummary?.prefix(120).description ?? "-")
                                .lineLimit(2)
                            if let fix = issue.fixInstructions, !fix.isEmpty {
                                Text(fix.prefix(80).description)
                                    .font(.caption)
                                    .foregroundStyle(.blue)
                                    .lineLimit(1)
                            }
                        }
                    }
                    .width(min: 250)

                    TableColumn("Status") { issue in
                        StatusBadge(resolved: issue.hasResolution)
                    }
                    .width(90)
                }
                .tableStyle(.bordered)
                .frame(minHeight: 300)
            }
        }
        .padding(16)
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .sheet(item: $selectedIssue) { issue in
            IssueDetailSheet(issue: issue)
        }
    }

    private func formatDate(_ dateStr: String?) -> String {
        guard let str = dateStr, str.count >= 16 else { return "-" }
        return String(str.prefix(16))
    }
}

struct StatusBadge: View {
    let resolved: Bool

    var body: some View {
        Text(resolved ? "Resolved" : "Open")
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(resolved ? Color.green.opacity(0.15) : Color.red.opacity(0.15))
            .foregroundStyle(resolved ? .green : .red)
            .clipShape(Capsule())
    }
}
