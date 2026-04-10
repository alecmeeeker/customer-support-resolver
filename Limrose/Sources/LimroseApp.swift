import SwiftUI

@main
struct LimroseApp: App {
    @State private var viewModel = DashboardViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView(viewModel: viewModel)
                .frame(minWidth: 800, minHeight: 500)
                .onAppear {
                    do {
                        try DatabaseManager.shared.setup()
                        DatabaseManager.shared.startWatching { [viewModel] in
                            viewModel.refresh()
                        }
                        viewModel.refresh()

                        // Sync .env file on launch so the Python pipeline has current config
                        if ConfigManager.shared.isConfigured {
                            try ConfigManager.shared.writeEnvFile()
                        }
                    } catch {
                        viewModel.errorMessage = "Failed to open database: \(error.localizedDescription)"
                    }
                }
        }
        .defaultSize(width: 1100, height: 750)
        .commands {
            CommandGroup(after: .toolbar) {
                Button("Refresh Dashboard") {
                    viewModel.refresh()
                }
                .keyboardShortcut("r", modifiers: .command)
            }
        }

        Settings {
            SettingsView()
        }
    }
}
