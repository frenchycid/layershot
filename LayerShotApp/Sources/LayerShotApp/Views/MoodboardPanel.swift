import SwiftUI
import UniformTypeIdentifiers

public struct MoodboardPanel: View {
    @Environment(AppState.self) private var appState
    @State private var showingAddProduct = false

    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Image(systemName: "photo.stack").foregroundStyle(.blue)
                Text("Moodboard").font(.headline)
                Spacer()
                if !appState.moodboardImages.isEmpty {
                    Text("\(appState.moodboardImages.count) images")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            .padding()

            Divider()

            MoodboardDropZone()

            Divider()

            HStack {
                Text("Produits").font(.subheadline.bold())
                Spacer()
                Button {
                    showingAddProduct = true
                } label: {
                    Image(systemName: "plus.circle.fill").foregroundStyle(.blue)
                }
                .buttonStyle(.plain)
                .help("Ajouter un produit")
            }
            .padding(.horizontal)
            .padding(.vertical, 10)

            ProductList()
            Spacer()
        }
        .sheet(isPresented: $showingAddProduct) {
            AddProductSheet(isPresented: $showingAddProduct)
        }
    }
}

struct MoodboardDropZone: View {
    @Environment(AppState.self) private var appState
    @State private var isTargeted = false

    var body: some View {
        Group {
            if appState.moodboardImages.isEmpty {
                dropPlaceholder
            } else {
                imageThumbnails
            }
        }
        .background(isTargeted ? Color.blue.opacity(0.08) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .strokeBorder(
                    isTargeted ? Color.blue : Color.gray.opacity(0.35),
                    style: StrokeStyle(lineWidth: 1.5, dash: [5])
                )
        )
        .padding(.horizontal)
        .padding(.vertical, 8)
        .onTapGesture { selectMoodboard() }
        .onDrop(of: [UTType.fileURL], isTargeted: $isTargeted) { providers in
            handleDrop(providers: providers)
        }
    }

    private var dropPlaceholder: some View {
        VStack(spacing: 8) {
            Image(systemName: "photo.on.rectangle.angled")
                .font(.system(size: 32)).foregroundStyle(.tertiary)
            Text("Glisser un dossier").font(.callout).foregroundStyle(.secondary)
            Text("ou cliquer pour choisir").font(.caption).foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity).frame(height: 160)
    }

    private var imageThumbnails: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 65))], spacing: 3) {
                ForEach(appState.moodboardImages, id: \.self) { url in
                    AsyncImage(url: url) { img in
                        img.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        Color.gray.opacity(0.2)
                    }
                    .frame(width: 65, height: 65)
                    .clipShape(RoundedRectangle(cornerRadius: 5))
                }
            }
            .padding(6)
        }
        .frame(height: 160)
    }

    private func selectMoodboard() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.message = "Sélectionner le dossier moodboard"
        if panel.runModal() == .OK, let url = panel.url {
            loadImages(from: url)
        }
    }

    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first else { return false }
        provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
            guard let data = item as? Data,
                  let url = URL(dataRepresentation: data, relativeTo: nil) else { return }
            DispatchQueue.main.async { loadImages(from: url) }
        }
        return true
    }

    private func loadImages(from url: URL) {
        appState.moodboardPath = url
        let exts = Set(["jpg", "jpeg", "png", "webp", "heic"])
        let images = (try? FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: nil))?
            .filter { exts.contains($0.pathExtension.lowercased()) }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
            ?? []
        appState.moodboardImages = images
    }
}

struct ProductList: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        List {
            if appState.products.isEmpty {
                Text("Cliquez + pour ajouter un produit")
                    .font(.caption).foregroundStyle(.tertiary).listRowSeparator(.hidden)
            } else {
                ForEach(appState.products) { product in
                    HStack(spacing: 8) {
                        Image(systemName: "shippingbox.fill").foregroundStyle(.orange).frame(width: 20)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(product.name).font(.callout)
                            Text(product.color).font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(product.cliArgument).font(.caption2.monospaced()).foregroundStyle(.tertiary)
                    }
                }
                .onDelete { indices in indices.forEach { appState.removeProduct(at: $0) } }
            }
        }
        .listStyle(.plain)
    }
}

struct AddProductSheet: View {
    @Environment(AppState.self) private var appState
    @Binding var isPresented: Bool
    @State private var name = ""
    @State private var color = ""
    @FocusState private var focused: Field?
    enum Field { case name, color }

    var canAdd: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        !color.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        VStack(spacing: 20) {
            Text("Ajouter un produit").font(.headline)

            VStack(alignment: .leading, spacing: 6) {
                Text("Nom").font(.caption).foregroundStyle(.secondary)
                TextField("ex: handbag", text: $name)
                    .textFieldStyle(.roundedBorder).focused($focused, equals: .name)
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Couleur").font(.caption).foregroundStyle(.secondary)
                TextField("ex: black", text: $color)
                    .textFieldStyle(.roundedBorder).focused($focused, equals: .color)
            }

            if canAdd {
                Text("Argument CLI : \(name.lowercased()):\(color.lowercased())")
                    .font(.caption2.monospaced()).foregroundStyle(.secondary)
            }

            HStack(spacing: 12) {
                Button("Annuler") { isPresented = false }
                    .buttonStyle(.bordered).keyboardShortcut(.cancelAction)
                Button("Ajouter") {
                    appState.addProduct(
                        name: name.trimmingCharacters(in: .whitespaces).lowercased(),
                        color: color.trimmingCharacters(in: .whitespaces).lowercased()
                    )
                    isPresented = false
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.defaultAction)
                .disabled(!canAdd)
            }
        }
        .padding(24).frame(width: 320)
        .onAppear { focused = .name }
    }
}
