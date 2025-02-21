import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.util.zip.InflaterInputStream;

public class Main {
  public static void main(String[] args) {
    System.err.println("Logs from your program will appear here!");

    final String command = args[0];

    switch (command) {
      case "init" -> {
        final File root = new File(".git");
        new File(root, "objects").mkdirs();
        new File(root, "refs").mkdirs();
        final File head = new File(root, "HEAD");

        try {
          head.createNewFile();
          Files.write(head.toPath(), "ref: refs/heads/main\n".getBytes());
          System.out.println("Initialized git directory");
        }
        catch (IOException e) {
          throw new RuntimeException(e);
        }
      }
      case "cat-file" -> {
        String hash = args[2];
        String dir = hash.substring(0, 2);
        String file = hash.substring(2);

        // open file
        File blobFile = new File("./.git/objects/" + dir + "/" + file);
        try {
          String blob = new BufferedReader(
              new InputStreamReader(new InflaterInputStream(new FileInputStream(blobFile))))
                  .readLine();
          String content = blob.substring(blob.indexOf('\0') + 1);
          System.out.print(content);
        }
        catch (IOException e) {
          throw new RuntimeException(e);
        }
      }
      default -> System.out.println("Unknown command: " + command);
    }
  }
}
