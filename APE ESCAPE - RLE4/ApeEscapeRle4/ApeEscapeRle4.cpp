#include <iostream>
#include <fstream>
#include <vector>

std::vector<uint8_t> decompress_rle4(const std::vector<uint8_t>& data, int width, int height) {
    std::vector<uint8_t> output_nibbles;
    int src = 0;
    int numpixels = 0;

    while (numpixels < width * height) {
        uint8_t nibble1 = data[src] >> 4;
        uint8_t nibble2 = data[src] & 0x0f;
        src++;

        if (nibble1 == nibble2) {
            int length = (data[src] + 2);
            src++;
            for (int i = 0; i < length; i++) {
                output_nibbles.push_back(nibble2);
                numpixels += 2;
            }
        }
        else {
            output_nibbles.push_back(nibble1);
            output_nibbles.push_back(nibble2);
            numpixels += 2;
        }
    }

    output_nibbles.resize(width * height);
    std::vector<uint8_t> output_bytes;
    for (size_t i = 0; i < output_nibbles.size(); i += 2) {
        output_bytes.push_back((output_nibbles[i] << 4) | output_nibbles[i + 1]);
    }

    return output_bytes;
}

void decompress_tim(const std::string& input_file_path, const std::string& output_file_path) {
    std::ifstream file(input_file_path, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Error opening file: " << input_file_path << std::endl;
        return;
    }

    // Read the first 4 bytes of the file
    char hdr[4];
    file.read(hdr, 4);
    uint8_t method = hdr[2];

    std::cout << "Method: " << std::hex << static_cast<int>(method) << std::endl;

    file.seekg(0x5c);
    int width = 4 * static_cast<int>(file.get()) | (static_cast<int>(file.get()) << 8);
    std::cout << "Width: " << width << std::endl;

    int height = 2 * static_cast<int>(file.get()) | (static_cast<int>(file.get()) << 8);
    std::cout << "Height: " << height / 2 << std::endl;

    std::vector<uint8_t> compressed_data((std::istreambuf_iterator<char>(file)), {});

    std::vector<uint8_t> decompressed_data;
    if (method == 0x02) {
        decompressed_data = decompress_rle4(compressed_data, width, height);
    }
    else {
        std::cerr << "Compression method not supported: " << static_cast<int>(method) << std::endl;
        return;
    }

   
    std::ofstream output_file(output_file_path, std::ios::binary);
    output_file.write(reinterpret_cast<const char*>(decompressed_data.data()), decompressed_data.size());

    std::cout << "Decompressed file saved as: " << output_file_path << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 4 || std::string(argv[1]) != "-d") {
        std::cerr << "Usage: " << argv[0] << " -d input_file compressed_output_file" << std::endl;
        return 1;
    }

    std::string input_file = argv[2];
    std::string output_file = argv[3];

    decompress_tim(input_file, output_file);

    return 0;
}
