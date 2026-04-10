import SwiftUI

struct IssueCategoriesSection: View {
    let categories: [CategoryStats]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Issue Categories", systemImage: "folder")
                .font(.headline)

            if categories.isEmpty {
                SectionPlaceholder(text: "No categories yet")
            } else {
                Table(categories) {
                    TableColumn("Category") { cat in
                        Text(cat.issueCategory ?? "Unknown")
                            .fontWeight(.medium)
                    }
                    .width(min: 120)

                    TableColumn("Count") { cat in
                        Text("\(cat.count)")
                            .monospacedDigit()
                    }
                    .width(60)

                    TableColumn("Resolved") { cat in
                        Text("\(cat.resolvedCount)")
                            .monospacedDigit()
                    }
                    .width(70)

                    TableColumn("Rate") { cat in
                        HStack(spacing: 6) {
                            Text(String(format: "%.1f%%", cat.resolutionRate))
                                .monospacedDigit()
                            RateIndicator(rate: cat.resolutionRate)
                        }
                    }
                    .width(80)
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

struct RateIndicator: View {
    let rate: Double

    var color: Color {
        if rate >= 75 { return .green }
        if rate >= 40 { return .orange }
        return .red
    }

    var body: some View {
        Circle()
            .fill(color)
            .frame(width: 8, height: 8)
    }
}

struct SectionPlaceholder: View {
    let text: String

    var body: some View {
        HStack {
            Spacer()
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.tertiary)
            Spacer()
        }
        .frame(height: 80)
    }
}
