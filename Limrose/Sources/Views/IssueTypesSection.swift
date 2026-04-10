import SwiftUI

struct IssueTypesSection: View {
    let issueTypes: [IssueTypeStats]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Top Issue Types", systemImage: "tag")
                .font(.headline)

            if issueTypes.isEmpty {
                SectionPlaceholder(text: "No issue types yet")
            } else {
                Table(issueTypes) {
                    TableColumn("Type") { row in
                        Text(row.issueType ?? "Unknown")
                            .fontWeight(.medium)
                    }
                    .width(min: 120)

                    TableColumn("Count") { row in
                        Text("\(row.count)")
                            .monospacedDigit()
                    }
                    .width(60)

                    TableColumn("Example") { row in
                        Text(row.exampleSummary?.prefix(80).description ?? "-")
                            .lineLimit(2)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .width(min: 150)
                }
                .tableStyle(.bordered)
                .frame(minHeight: 200)
            }
        }
        .padding(16)
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}
