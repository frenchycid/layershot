import SwiftUI
import LayerShotApp
import Observation

@main
struct LayerShotApp: App {
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup("LayerShot") {
            ContentView()
                .environment(appState)
        }
        .defaultSize(width: 1400, height: 900)

        Settings {
            SettingsView()
                .environment(appState)
        }
    }
}

struct SettingsView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        @Bindable var state = appState
        Form {
            Section("Python") {
                TextField("Chemin Python", text: $state.pythonPath)
            }
            Section("Projet LayerShot") {
                TextField("Chemin du projet", text: $state.projectPath)
                Button("Parcourir...") {
                    let panel = NSOpenPanel()
                    panel.canChooseDirectories = true
                    panel.canChooseFiles = false
                    if panel.runModal() == .OK, let url = panel.url {
                        appState.projectPath = url.path
                    }
                }
            }
        }
        .formStyle(.grouped)
        .frame(width: 450)
    }
}
