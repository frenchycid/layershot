import SwiftUI

public struct LoginView: View {
    @Environment(AppState.self) private var appState
    @State private var apiKey: String = ""
    @State private var isChecking: Bool = false
    @State private var errorMessage: String? = nil

    public init() {}

    public var body: some View {
        VStack(spacing: 24) {
            header
            Divider()
            apiKeySection
            orDivider
            cliSection
            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
            }
        }
        .padding(28)
        .frame(width: 380)
        .onAppear { apiKey = appState.claudeApiKey }
    }

    // MARK: - Subviews

    private var header: some View {
        VStack(spacing: 8) {
            Image(systemName: "camera.aperture")
                .font(.system(size: 36))
                .foregroundStyle(.blue)
            Text("LayerShot")
                .font(.title2.bold())
            Text("Connectez-vous avec votre clé API Anthropic\nou via Claude Code CLI.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }

    private var apiKeySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Clé API Anthropic", systemImage: "key")
                .font(.caption.bold())
                .foregroundStyle(.secondary)
            SecureField("sk-ant-...", text: $apiKey)
                .textFieldStyle(.roundedBorder)
                .font(.system(.body, design: .monospaced))
            Button {
                Task { await connectWithApiKey() }
            } label: {
                if isChecking {
                    ProgressView().scaleEffect(0.75)
                } else {
                    Text("Connexion avec la clé API")
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(apiKey.trimmingCharacters(in: .whitespaces).isEmpty || isChecking)
            .frame(maxWidth: .infinity)
        }
    }

    private var orDivider: some View {
        HStack {
            Rectangle().frame(height: 1).foregroundStyle(.quaternary)
            Text("ou").font(.caption).foregroundStyle(.tertiary)
            Rectangle().frame(height: 1).foregroundStyle(.quaternary)
        }
    }

    private var cliSection: some View {
        VStack(spacing: 8) {
            Text("Claude Code CLI")
                .font(.caption.bold())
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            Button {
                Task { await connectWithCLI() }
            } label: {
                Label("Ouvrir claude login", systemImage: "terminal")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(isChecking)
            .frame(maxWidth: .infinity)

            Button {
                Task { await checkCLIAuth() }
            } label: {
                Label("Vérifier l'authentification CLI", systemImage: "checkmark.shield")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.plain)
            .foregroundStyle(.blue)
            .disabled(isChecking)
        }
    }

    // MARK: - Actions

    @MainActor
    private func connectWithApiKey() async {
        isChecking = true
        errorMessage = nil
        let key = apiKey.trimmingCharacters(in: .whitespaces)
        guard key.hasPrefix("sk-ant-") else {
            errorMessage = "Clé invalide — doit commencer par « sk-ant- »."
            isChecking = false
            return
        }
        appState.claudeApiKey = key
        appState.isAuthenticated = true
        isChecking = false
    }

    @MainActor
    private func connectWithCLI() async {
        isChecking = true
        errorMessage = nil
        do {
            let runner = PipelineRunner(pythonPath: appState.pythonPath, projectPath: appState.projectPath)
            _ = try await runner.run(command: ["claude", "login"]) { _ in }
            appState.isAuthenticated = true
        } catch {
            errorMessage = "Échec : \(error.localizedDescription)"
        }
        isChecking = false
    }

    @MainActor
    private func checkCLIAuth() async {
        isChecking = true
        errorMessage = nil
        do {
            let runner = PipelineRunner(pythonPath: appState.pythonPath, projectPath: appState.projectPath)
            _ = try await runner.run(command: ["claude", "--version"]) { _ in }
            appState.isAuthenticated = true
        } catch {
            errorMessage = "Claude CLI introuvable ou non authentifié."
        }
        isChecking = false
    }
}
