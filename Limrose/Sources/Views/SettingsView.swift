import SwiftUI

struct SettingsView: View {
    @State private var config = ConfigManager.shared
    @AppStorage("dataDirPath") private var dataDirPath: String = ""
    @State private var showApiKey = false
    @State private var showOpenAIKey = false
    @State private var saveStatus: SaveStatus = .idle

    private enum SaveStatus: Equatable {
        case idle
        case saved
        case error(String)
    }

    private var defaultPath: String {
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask
        ).first!
        return appSupport.appendingPathComponent("Limrose").path
    }

    var body: some View {
        TabView {
            generalTab
                .tabItem { Label("General", systemImage: "gearshape") }

            advancedTab
                .tabItem { Label("Advanced", systemImage: "slider.horizontal.3") }
        }
        .frame(width: 520, height: 500)
    }

    // MARK: - General Tab

    private var generalTab: some View {
        Form {
            Section("LLM Configuration") {
                Picker("Provider", selection: $config.llmProvider) {
                    Text("Gemini").tag("GEMINI")
                    Text("DeepSeek").tag("DEEPSEEK")
                }
                .pickerStyle(.segmented)

                HStack {
                    if showApiKey {
                        TextField("API Key", text: $config.llmApiKey)
                            .textFieldStyle(.roundedBorder)
                    } else {
                        SecureField("API Key", text: $config.llmApiKey)
                            .textFieldStyle(.roundedBorder)
                    }
                    Button(action: { showApiKey.toggle() }) {
                        Image(systemName: showApiKey ? "eye.slash" : "eye")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .help(showApiKey ? "Hide API key" : "Show API key")
                }

                if config.llmApiKey.isEmpty {
                    Label("An API key is required to run the email pipeline.", systemImage: "exclamationmark.triangle.fill")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }

                TextField(
                    "Model",
                    text: $config.llmModel,
                    prompt: Text(config.defaultModel)
                )
                .textFieldStyle(.roundedBorder)

                Text("Leave blank for default: \(config.defaultModel)")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                if config.llmProvider == "DEEPSEEK" {
                    TextField(
                        "API URL",
                        text: $config.llmApiUrl,
                        prompt: Text(config.defaultApiUrl)
                    )
                    .textFieldStyle(.roundedBorder)

                    Text("Leave blank for default DeepSeek endpoint.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Section("Database Location") {
                TextField("Data directory", text: $dataDirPath, prompt: Text(defaultPath))
                    .textFieldStyle(.roundedBorder)

                Text("Leave blank to use the default: \(defaultPath)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Section("About") {
                LabeledContent("Version", value: "1.0.0")
                LabeledContent("Database Engine", value: "SQLite (WAL mode)")
                LabeledContent("License", value: "AOSL 1.0")
            }

            Section {
                HStack {
                    Button("Save Configuration") {
                        do {
                            try config.save()
                            saveStatus = .saved
                            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                                if saveStatus == .saved { saveStatus = .idle }
                            }
                        } catch {
                            saveStatus = .error(error.localizedDescription)
                        }
                    }
                    .buttonStyle(.borderedProminent)

                    switch saveStatus {
                    case .idle:
                        EmptyView()
                    case .saved:
                        Label("Saved", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                            .font(.caption)
                    case .error(let msg):
                        Label(msg, systemImage: "xmark.circle.fill")
                            .foregroundStyle(.red)
                            .font(.caption)
                            .lineLimit(2)
                    }
                }
            }
        }
        .formStyle(.grouped)
    }

    // MARK: - Advanced Tab

    private var advancedTab: some View {
        Form {
            Section("Offline Mode") {
                Toggle("Hugging Face offline mode", isOn: $config.hfOffline)
                Toggle("Transformers offline mode", isOn: $config.transformersOffline)
                Text("Use cached models only — no internet required for embeddings.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Section("Additional API Keys") {
                HStack {
                    if showOpenAIKey {
                        TextField("OpenAI API Key (optional)", text: $config.openaiApiKey)
                            .textFieldStyle(.roundedBorder)
                    } else {
                        SecureField("OpenAI API Key (optional)", text: $config.openaiApiKey)
                            .textFieldStyle(.roundedBorder)
                    }
                    Button(action: { showOpenAIKey.toggle() }) {
                        Image(systemName: showOpenAIKey ? "eye.slash" : "eye")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
                Text("Only needed if using OpenAI for agent processing.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
    }
}
