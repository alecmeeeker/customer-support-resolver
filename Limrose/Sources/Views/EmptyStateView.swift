import SwiftUI

struct EmptyStateView: View {
    var onRefresh: () -> Void

    private var isConfigured: Bool {
        ConfigManager.shared.isConfigured
    }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "tray")
                .font(.system(size: 56))
                .foregroundStyle(.quaternary)

            VStack(spacing: 8) {
                Text("No Issues Tracked Yet")
                    .font(.title.bold())

                Text("Run the email pipeline to populate the dashboard with customer issue data.")
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 400)
            }

            // Setup steps
            VStack(alignment: .leading, spacing: 14) {
                StepRow(number: 1, text: "Configure Gmail OAuth", detail: "python setup_oauth.py")
                StepRow(
                    number: 2,
                    text: "Set your LLM API key",
                    detail: "Open Settings (\u{2318},) \u{2192} enter your API key",
                    status: isConfigured ? .done : .pending
                )
                StepRow(number: 3, text: "Run the pipeline", detail: "./update_emails_v2.sh")
                StepRow(number: 4, text: "Data appears here automatically", detail: "Dashboard auto-refreshes on changes")
            }
            .padding(20)
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            HStack(spacing: 12) {
                Button(action: {
                    NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
                }) {
                    Label("Open Settings", systemImage: "gearshape")
                }

                Button(action: {
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString("./update_emails_v2.sh", forType: .string)
                }) {
                    Label("Copy Pipeline Command", systemImage: "doc.on.doc")
                }

                Button(action: onRefresh) {
                    Label("Check Again", systemImage: "arrow.clockwise")
                }
                .buttonStyle(.borderedProminent)
            }

            Spacer()
        }
        .padding(40)
    }
}

private struct StepRow: View {
    let number: Int
    let text: String
    let detail: String
    var status: StepStatus = .neutral

    enum StepStatus {
        case neutral, done, pending
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Image(systemName: "\(number).circle.fill")
                    .font(.title3)
                    .foregroundStyle(iconColor)
                    .frame(width: 24)

                if status == .done {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.caption2)
                        .foregroundStyle(.green)
                        .offset(x: 10, y: -8)
                }
                if status == .pending {
                    Image(systemName: "exclamationmark.circle.fill")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                        .offset(x: 10, y: -8)
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(text)
                    .font(.body.weight(.medium))
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fontDesign(.monospaced)
            }
        }
    }

    private var iconColor: Color {
        switch status {
        case .done: .green
        case .pending: .orange
        case .neutral: .blue
        }
    }
}
