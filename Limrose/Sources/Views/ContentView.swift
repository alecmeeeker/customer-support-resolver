import SwiftUI

struct ContentView: View {
    var viewModel: DashboardViewModel

    var body: some View {
        Group {
            if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundStyle(.red)
                    Text("Database Error")
                        .font(.title2.bold())
                    Text(error)
                        .font(.body)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                    Button("Retry") { viewModel.refresh() }
                        .buttonStyle(.borderedProminent)
                }
                .padding(40)
            } else if viewModel.isEmpty && !viewModel.isLoading {
                EmptyStateView(onRefresh: { viewModel.refresh() })
            } else {
                DashboardView(viewModel: viewModel)
            }
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button(action: { viewModel.refresh() }) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .help("Refresh dashboard data")
            }
            ToolbarItem(placement: .automatic) {
                if viewModel.isLoading {
                    ProgressView()
                        .controlSize(.small)
                } else if let time = viewModel.lastRefresh {
                    Text(time, style: .relative)
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }
        }
    }
}
