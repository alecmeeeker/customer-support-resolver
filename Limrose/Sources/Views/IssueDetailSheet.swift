import SwiftUI

struct IssueDetailSheet: View {
    let issue: CustomerIssue
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(issue.issueType ?? "Issue")
                        .font(.title2.bold())
                    HStack(spacing: 8) {
                        if let category = issue.issueCategory {
                            Text(category)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(.blue.opacity(0.1))
                                .foregroundStyle(.blue)
                                .clipShape(Capsule())
                        }
                        StatusBadge(resolved: issue.hasResolution)
                        if let confidence = issue.confidenceLevel {
                            Text(confidence)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            .padding(20)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Summary
                    if let summary = issue.issueSummary, !summary.isEmpty {
                        DetailSection(title: "Summary", icon: "text.alignleft") {
                            Text(summary)
                                .font(.body)
                                .textSelection(.enabled)
                        }
                    }

                    // Resolution
                    if let resolution = issue.resolutionSummary, !resolution.isEmpty {
                        DetailSection(title: "Resolution", icon: "checkmark.seal") {
                            Text(resolution)
                                .font(.body)
                                .textSelection(.enabled)
                        }
                    }

                    // Fix instructions
                    if let fix = issue.fixInstructions, !fix.isEmpty {
                        DetailSection(title: "Fix Instructions", icon: "wrench.and.screwdriver") {
                            Text(fix)
                                .font(.system(.body, design: .monospaced))
                                .textSelection(.enabled)
                                .padding(12)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.blue.opacity(0.05))
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                    }

                    // Metadata
                    DetailSection(title: "Details", icon: "info.circle") {
                        Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 8) {
                            if let date = issue.createdAt {
                                GridRow {
                                    Text("Created").foregroundStyle(.secondary)
                                    Text(String(date.prefix(19)))
                                }
                            }
                            if let score = issue.similarityScore, score > 0 {
                                GridRow {
                                    Text("Similarity").foregroundStyle(.secondary)
                                    Text(String(format: "%.2f", score))
                                }
                            }
                            if let based = issue.basedOnIssues, !based.isEmpty {
                                GridRow {
                                    Text("Based on").foregroundStyle(.secondary)
                                    Text(based).lineLimit(3)
                                }
                            }
                        }
                        .font(.callout)
                    }
                }
                .padding(20)
            }
        }
        .frame(width: 600, height: 500)
    }
}

private struct DetailSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: icon)
                .font(.headline)
            content
        }
    }
}
